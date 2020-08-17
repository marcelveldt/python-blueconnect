"""Unofficial python library for the Blue Riiot Blue Connect API."""


import asyncio
import time
import json
import logging

import aiohttp
from aws_request_signer import AwsRequestSigner

AWS_REGION = "eu-west-1"
AWS_SERVICE = "execute-api"
BASE_HEADERS = {
    "User-Agent": "BlueConnect/3.2.1",
    "Accept-Language": "en-DK;q=1.0, da-DK;q=0.9",
    "Accept": "*/*"
}
BASE_URL = "https://api.riiotlabs.com/prod/"
LOGGER = logging.getLogger()


class BlueConnectApi():
    """Class that holds the connection to the Blue Connect API."""
    _username = None
    _password = None
    _language = None
    _token_info = {}
    _loop = None
    _http_session = None
    _user_info = {}
    _swimming_pool_info = {}
    _swimming_pool_status = {}
    _swimming_pool_feed = {}
    _swimming_pool_ph = {}
    _swimming_pool_orp = {}
    _swimming_pool_temp = {}
    _swimming_pool_device = {}

    def __init__(self, username: str, password: str, language: str = "en") -> None:
        """Inititialize the api connection, a valid username and password must be provided."""
        self._username = username
        self._password = password
        self._language = language
        self._loop = asyncio.get_event_loop()
        self._http_session = aiohttp.ClientSession(
            loop=self._loop, connector=aiohttp.TCPConnector()
        )

    def close(self):
        """Close connection to the api."""
        asyncio.create_task(self.close_async())

    async def close_async(self):
        """Close connection to the api."""
        await self._http_session.close()

    async def fetch_data(self):
        """Fetch latest state from API."""
        self._user_info = await self.get_user_info()
        self._swimming_pool_info = await self.get_swimming_pool_info(self.main_swimming_pool_id)
        self._swimming_pool_status = await self.get_swimming_pool_status(self.main_swimming_pool_id)
        self._swimming_pool_feed = await self.get_swimming_pool_feed(self.main_swimming_pool_id)
        self._swimming_pool_device = await self.get_swimming_pool_blue_device(self.main_swimming_pool_id)
        # get levels from status task infos
        for task in self.swimming_pool_status["tasks"]:
            if task["task_identifier"].startswith("ORP_"):
                self._swimming_pool_orp = json.loads(task["data"])
            if task["task_identifier"].startswith("TEMPERATURE_"):
                self._swimming_pool_temp = json.loads(task["data"])
            if task["task_identifier"].startswith("PH_"):
                self._swimming_pool_ph = json.loads(task["data"])

    @property
    def main_swimming_pool_id(self):
        """Return ID of the main swimming pool."""
        return self.user_preferences.get("main_swimming_pool_id")

    @property
    def swimming_pool_name(self):
        """Return name of the main swimming pool."""
        return self.swimming_pool_info.get("name")

    @property
    def temperature_unit(self):
        """Return temperature_unit preference of the logged in user."""
        return self.user_preferences.get("display_temperature_unit")

    @property
    def swimming_pool_info(self):
        """Return info for the main swimming pool."""
        return self._swimming_pool_info

    @property
    def swimming_pool_status(self):
        """Return info for the main swimming pool."""
        return self._swimming_pool_status

    @property
    def swimming_pool_feed(self):
        """Return status feed for the main swimming pool."""
        return self._swimming_pool_feed

    @property
    def swimming_pool_device(self):
        """Return Blue Connect device info for the main swimming pool."""
        return self._swimming_pool_device

    @property
    def user_info(self):
        """Return info about logged in user."""
        return self._user_info

    @property
    def user_preferences(self):
        """Return preferences of logged in user."""
        return self._user_info.get("userPreferences", {})

    @property
    def swimming_pool_ph(self):
        """Return current PH info of the main swimming pool."""
        return self._swimming_pool_ph

    @property
    def swimming_pool_orp(self):
        """Return current ORP info of the main swimming pool."""
        return self._swimming_pool_orp

    @property
    def swimming_pool_temp(self):
        """Return current Temperature info of the main swimming pool."""
        return self._swimming_pool_temp

    async def get_user_info(self):
        """Retrieve details of logged in user."""
        return await self.__get_data("user")

    async def get_swimming_pool_info(self, swimming_pool_id: str):
        """Retrieve details for a specific swimming pool."""
        return await self.__get_data(f"swimming_pool/{swimming_pool_id}")

    async def get_swimming_pool_status(self, swimming_pool_id: str):
        """Retrieve status for a specific swimming pool."""
        return await self.__get_data(f"swimming_pool/{swimming_pool_id}/status")

    async def get_swimming_pool_blue_device(self, swimming_pool_id: str):
        """Retrieve Blue device info for a specific swimming pool."""
        return await self.__get_data(f"swimming_pool/{swimming_pool_id}/blue")

    async def get_swimming_pool_feed(self, swimming_pool_id: str):
        """Retrieve feed for a specific swimming pool, defaults to user's main swimming pool."""
        return await self.__get_data(f"swimming_pool/{swimming_pool_id}/feed?lang={self._language}")

    async def __get_credentials(self):
        """Retrieve auth credentials by logging in with username/password."""
        if self._token_info and self._token_info["expires"] > time.time():
            # return cached credentials if still valid
            return self._token_info["credentials"]
        # perform log-in to get credentials
        url = BASE_URL + "user/login"
        async with self._http_session.post(
            url, json={"email": self._username, "password": self._password}
        ) as response:
            if response.status != 200:
                LOGGER.exception(await response.text())
                return None
            result = await response.json()
            self._token_info = result
            self._token_info["expires"] = time.time() + 3500
            return result["credentials"]

    async def __get_data(self, endpoint, params={}):
        """Get data from api."""
        url = BASE_URL + endpoint
        headers = BASE_HEADERS.copy()
        # sign the request
        creds = await self.__get_credentials()
        if not creds:
            return None
        request_signer = AwsRequestSigner(
            AWS_REGION, creds["access_key"], creds["secret_key"], AWS_SERVICE
        )
        headers.update(
            request_signer.sign_with_headers("GET", url, headers)
        )
        headers["X-Amz-Security-Token"] = creds["session_token"]
        async with self._http_session.get(
            url, headers=headers, params=params, verify_ssl=False
        ) as response:
            assert response.status == 200
            return await response.json()
