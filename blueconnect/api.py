"""Unofficial python library for the Blue Riiot Blue Connect API."""

import asyncio
import time
from typing import List, Optional

import aiohttp
from aws_request_signer import AwsRequestSigner

from .models import (
    BlueDevice,
    SwimmingPool,
    SwimmingPoolFeed,
    SwimmingPoolLastMeasurements,
    SwimmingPoolStatus,
    User,
)

AWS_REGION = "eu-west-1"
AWS_SERVICE = "execute-api"
BASE_HEADERS = {
    "User-Agent": "BlueConnect/3.2.1",
    "Accept-Language": "en-DK;q=1.0, da-DK;q=0.9",
    "Accept": "*/*",
}
BASE_URL = "https://api.riiotlabs.com/prod/"


class BlueConnectApi:
    """Class that holds the connection to the Blue Connect API."""

    def __init__(self, username: str, password: str) -> None:
        """Inititialize the api connection, a valid username and password must be provided."""
        self._username = username
        self._password = password
        self._http_session = aiohttp.ClientSession(connector=aiohttp.TCPConnector())
        self._token_info = {}

    def close(self) -> None:
        """Close connection to the api."""
        if asyncio.get_event_loop().is_running():
            asyncio.create_task(self.close_async())
        else:
            asyncio.get_event_loop().run_until_complete(self.close_async())

    async def close_async(self) -> None:
        """Close connection to the api."""
        await self._http_session.close()

    async def get_user(self) -> User:
        """Retrieve details of logged-in user."""
        data = await self.__get_data(f"user")
        return User.from_json(data)

    async def get_blue_device(self, blue_device_serial: str) -> BlueDevice:
        """Retrieve details for a specific blue device."""
        data = await self.__get_data(f"blue/{blue_device_serial}")
        return BlueDevice.from_json(data)

    async def get_swimming_pools(self) -> List[SwimmingPool]:
        """Retrieve all swimming pools."""
        data = await self.__get_data(f"swimming_pool")
        return [SwimmingPool.from_json(item["swimming_pool"]) for item in data["data"]]

    async def get_swimming_pool(self, swimming_pool_id: str) -> SwimmingPool:
        """Retrieve details for a specific swimming pool."""
        data = await self.__get_data(f"swimming_pool/{swimming_pool_id}")
        return SwimmingPool.from_json(data)

    async def get_swimming_pool_status(
        self, swimming_pool_id: str
    ) -> SwimmingPoolStatus:
        """Retrieve status for a specific swimming pool."""
        data = await self.__get_data(f"swimming_pool/{swimming_pool_id}/status")
        return SwimmingPoolStatus.from_json(data)

    async def get_swimming_pool_blue_devices(
        self, swimming_pool_id: str
    ) -> List[BlueDevice]:
        """Retrieve Blue devices for a specific swimming pool."""
        data = await self.__get_data(f"swimming_pool/{swimming_pool_id}/blue")
        result = []
        for item in data["data"]:
            blue_device = await self.get_blue_device(item["blue_device_serial"])
            result.append(blue_device)
        return result

    async def get_swimming_pool_feed(
        self, swimming_pool_id: str, language: str = "en"
    ) -> SwimmingPoolFeed:
        """Retrieve feed for a specific swimming pool."""
        data = await self.__get_data(
            f"swimming_pool/{swimming_pool_id}/feed?lang={language}"
        )
        return SwimmingPoolFeed.from_json(data)

    async def get_last_measurements(
        self, swimming_pool_id: str, blue_device_serial: str
    ) -> SwimmingPoolLastMeasurements:
        """Retrieve last measurements for a specific swimming pool."""
        data = await self.__get_data(
            f"swimming_pool/{swimming_pool_id}/blue/{blue_device_serial}/lastMeasurements?mode=blue_and_strip"
        )
        return SwimmingPoolLastMeasurements.from_json(data)

    async def __get_credentials(self) -> dict:
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
                error_msg = await response.text()
                raise Exception("Error logging in user: %s" % error_msg)
            result = await response.json()
            self._token_info = result
            self._token_info["expires"] = time.time() + 3500
            return result["credentials"]

    async def __get_data(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Get data from api."""
        if params is None:
            params = {}
        url = BASE_URL + endpoint
        headers = BASE_HEADERS.copy()
        # sign the request
        creds = await self.__get_credentials()
        request_signer = AwsRequestSigner(
            AWS_REGION, creds["access_key"], creds["secret_key"], AWS_SERVICE
        )
        headers.update(request_signer.sign_with_headers("GET", url, headers))
        headers["X-Amz-Security-Token"] = creds["session_token"]
        async with self._http_session.get(
            url, headers=headers, params=params, verify_ssl=False
        ) as response:
            if response.status != 200:
                error_msg = await response.text()
                raise Exception(
                    "Error while retrieving data for endpoint %s: %s"
                    % (endpoint, error_msg)
                )
            return await response.json()
