"""Tests for Blue Connect api library."""

from ..blueconnect import BlueConnectSimpleAPI
import pytest

api = BlueConnectSimpleAPI("test", "test", "nl")

# TODO TODO TODO

@pytest.mark.asyncio
async def test_base():
    print(api.measurements)
