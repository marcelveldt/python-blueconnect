"""Models for Blue Connect API objects."""

import json
from dataclasses import dataclass, fields
from datetime import datetime
from enum import Enum
from typing import List

import inflection
from dateutil.parser import isoparse


def transform_value(value, value_type):
    """Helper method to transform raw api value to correct type."""
    if value_type in (str, int, float, bool):
        return value
    if value_type == datetime:
        return isoparse(value)
    if isinstance(value, list):
        item_type = value_type.__args__[0]
        return [transform_value(item, item_type) for item in value]
    if hasattr(value_type, "from_json"):
        return value_type.from_json(value)
    return value_type(value)


class ModelBase:
    """Common base for our models."""

    @classmethod
    def from_json(cls, json_obj):
        """Raw json/dict values from api to instance attributes."""
        # convert json to python dict
        if not isinstance(json_obj, dict):
            json_obj = json.loads(json_obj)
        # extract needed init values from provided json data
        cls_attr = {}
        for key, value in json_obj.items():
            # make sure we have snake case attribute names
            pythonic_key = inflection.underscore(key)
            cls_field = next((x for x in fields(cls) if x.name == pythonic_key), None)
            if not cls_field:
                continue
            cls_attr[pythonic_key] = transform_value(value, cls_field.type)
        return cls(**cls_attr)


@dataclass
class BlueDevice(ModelBase):
    """Model for a Blue Connect device."""

    serial: str
    hw_generation: int
    hw_product_type: str
    hw_product_name: str
    last_measure_ble: datetime
    last_measure_sigfox: datetime
    battery_low: bool


class MeasurementTrend(Enum):
    """Enum for a measurement trend."""

    STABLE = "stable"
    INCREASE = "increase"
    DECREASE = "decrease"
    UNDEFINED = "undefined"


@dataclass
class SwimmingPoolMeasurement(ModelBase):
    """Model for a swimming pool measurement."""

    name: str
    priority: int
    timestamp: datetime
    expired: bool
    value: float
    trend: MeasurementTrend
    ok_min: float
    ok_max: float
    warning_high: float
    warning_low: float
    gauge_max: float
    gauge_min: float
    issuer: str


@dataclass
class SwimmingPoolLastMeasurements(ModelBase):
    """Model for swimming pool last measurements data."""

    status: str
    swimming_pool_id: str
    data: List[SwimmingPoolMeasurement]
    blue_device_serial: str = ""
    last_blue_measure_timestamp: datetime = None
    last_strip_timestamp: datetime = None

    @property
    def measurements(self):
        """Convenience attribute to get all (current) measurements."""
        return self.data


@dataclass
class UserInfo(ModelBase):
    """Model for UserInfo."""

    user_id: str
    first_name: str
    last_name: str
    email: str
    account_type: str


class TemperatureUnit(Enum):
    """Enum for TemperatureUnit."""

    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"


@dataclass
class UserPreferences(ModelBase):
    """Model for UserPreferences."""

    display_temperature_unit: TemperatureUnit
    display_unit_system: str
    main_swimming_pool_id: str


@dataclass
class User(ModelBase):
    """Model for a User."""

    user_info: UserInfo
    user_preferences: UserPreferences


@dataclass
class SwimmingPool(ModelBase):
    """Model for a SwimmingPool."""

    updated: datetime
    swimming_pool_id: str
    created: datetime
    name: str
    last_refresh_status: datetime


@dataclass
class SwimmingPoolStatusTask(ModelBase):
    """Model for a SwimmingPoolStatusTask."""

    status_id: str
    since: datetime
    data: dict
    swimming_pool_id: str
    created: datetime
    task_identifier: str
    update_reason: str
    order: int


@dataclass
class SwimmingPoolStatus(ModelBase):
    """Model for SwimmingPoolStatus."""

    since: datetime
    status_id: str
    global_status_code: str
    swimming_pool_id: str
    created: str
    update_reason: str
    blue_device_serial: str
    last_notif_date: str
    swimming_pool_name: str
    tasks: List[SwimmingPoolStatusTask]


@dataclass
class SwimmingPoolFeedMessage(ModelBase):
    """Model for a SwimmingPoolFeedMessage."""

    id: str
    title: str
    message: str


@dataclass
class SwimmingPoolFeed(ModelBase):
    """Model for a SwimmingPoolFeedMessage."""

    swimming_pool_id: str
    timestamp: datetime
    data: List[SwimmingPoolFeedMessage]
    lang: str

    @property
    def messages(self):
        """Convenience attribute to get all feed messages."""
        return self.data

    @property
    def current_message(self):
        """Return the last/current feedmessage."""
        return self.data[0] if self.data else None
