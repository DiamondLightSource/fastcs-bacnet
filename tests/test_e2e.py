# End-to-End (e2e) tests of fastcs-bacnet
import asyncio
from collections.abc import AsyncGenerator

import aioca
import pytest

from fastcs_bacnet.core.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)
from fastcs_bacnet.core.fastcs_bacnet import fastcs_bacnet

from .conftest import DeviceData


@pytest.fixture
async def fastcs_application(
    bacnet_servers: None,
    device_data: list[DeviceData],
) -> AsyncGenerator[None]:
    """The main application under test.

    Runs in a background task"""

    subscriptions: dict[SubscriptionID, str] = {}

    for device in device_data:
        addr = IPv4SocketAddress(device.device_ip, device.device_port, device.device_id)
        for object in device.object_data:
            obj_id = ObjectIdentifier(object.object_type, object.object_instance)
            subscriptions.update({SubscriptionID(addr, obj_id): object.pv})

    task = asyncio.create_task(fastcs_bacnet(subscriptions))
    yield
    task.cancel()
    await task


async def test_all_object_creation_subscription(
    device_data: list[DeviceData],
    fastcs_application: None,
):
    """Check that the FastCS application can retrieve all expected PVs from all
    configured Devices"""

    for i, device in enumerate(device_data):
        for object in device.object_data:
            val = await aioca.caget(f"FASTCS_BACNET:Subcontroller{i}:{object.pv}")
            assert val == object.expected_value, (
                f"Did not find expected value for device {device.device_name} "
                f"object {object}"
            )
