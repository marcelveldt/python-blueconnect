"""Unofficial python library for the Blue Riiot Blue Connect API."""

import asyncio
from typing import List

from .api import BlueConnectApi
from .models import (
    BlueDevice,
    SwimmingPool,
    SwimmingPoolFeedMessage,
    SwimmingPoolMeasurement,
    TemperatureUnit,
)


class BlueConnectSimpleAPI:
    """Class that provides a common structure around the Blue Connect API for a single/main swimming pool."""

    def __init__(self, username: str, password: str, language: str = "en") -> None:
        """Inititialize the api connection, a valid username and password must be provided."""
        self._api = BlueConnectApi(username, password)
        self._language = language
        self._temperature_unit = None
        self._pool_info = None
        self._pool_feed_message = None
        self._pool_blue_device = None
        self._pool_measurements = []

    def close(self) -> None:
        """Close connection to the api."""
        self._api.close()

    async def fetch_data(self) -> None:
        """Fetch latest state from API."""
        user_info = await self._api.get_user()
        main_pool_id = user_info.user_preferences.main_swimming_pool_id
        self._temperature_unit = user_info.user_preferences.display_temperature_unit
        self._pool_info = await self._api.get_swimming_pool(main_pool_id)
        self._pool_feed_message = (
            await self._api.get_swimming_pool_feed(main_pool_id, self._language)
        ).current_message
        blue_devices = await self._api.get_swimming_pool_blue_devices(main_pool_id)
        self._pool_blue_device = blue_devices[0] if blue_devices else None
        if self._pool_blue_device:
            self._pool_measurements = (
                await self._api.get_last_measurements(
                    main_pool_id, self._pool_blue_device.serial
                )
            ).measurements

    @property
    def pool(self) -> SwimmingPool:
        """Return full details of the (main) swimming pool."""
        return self._pool_info

    @property
    def temperature_unit(self) -> TemperatureUnit:
        """Return temperature unit of the temperature measurements."""
        return self._temperature_unit

    @property
    def feed_message(self) -> SwimmingPoolFeedMessage:
        """Return the (latest) feed/health message for the (main) swimming pool."""
        return self._pool_feed_message

    @property
    def blue_device(self) -> BlueDevice:
        """Return Blue Connect device info for the (main) swimming pool."""
        return self._pool_blue_device

    @property
    def measurements(self) -> List[SwimmingPoolMeasurement]:
        """Return all last/current measurements for the (main) swimming pool."""
        return self._pool_measurements
