# End-to-End (e2e) tests of fastcs-bacnet
import asyncio
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import aioca
import pytest

from fastcs_bacnet.core.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)
from fastcs_bacnet.core.fastcs_bacnet import fastcs_bacnet
from fastcs_bacnet.dummy.BAC0.device import Device
from fastcs_bacnet.dummy.generic.device_variables.constant_variable import (
    ConstantVariable,
)

# TODO: We need a new release of BAC0 that includes
# f702eb6301aee9d10a4046a59505d1ab42801770
# BAC0.log_level(logger="warning", stdout="critical", stderr="critical")

BACNET_SERVER_IP = "127.0.0.1"
BACNET_SERVER_PORT = 47809
BACNET_SERVER_DEVICEID = 456


@dataclass
class ObjectData:
    object_type: str
    object_instance: int
    expected_value: bool | float
    pv: str


@pytest.fixture
def test_data() -> list[ObjectData]:
    return [
        ObjectData("analog-output", 0, 1.23, "abc-1"),
        ObjectData("analog-output", 1, 2.34, "ao-2"),
        ObjectData("analog-output", 2, 3.45, "analog-output-3"),
    ]


@pytest.fixture
def subscriptions(test_data: list[ObjectData]) -> dict[SubscriptionID, str]:
    """A list of subscriptions for our bacnet server to set up
    and our test client to subscribe to"""
    ipv4address = IPv4SocketAddress(
        BACNET_SERVER_IP, BACNET_SERVER_PORT, BACNET_SERVER_DEVICEID
    )

    subscriptions = {}

    for data in test_data:
        subscriptions.update(
            {
                SubscriptionID(
                    ipv4address,
                    ObjectIdentifier(data.object_type, data.object_instance),
                ): data.pv
            }
        )

    return subscriptions


@pytest.fixture
async def bacnet_server(
    test_data: list[ObjectData],
    subscriptions: dict[SubscriptionID, str],
) -> AsyncGenerator[Device]:
    """A BACnet server, simulating a real device"""
    device = Device(
        BACNET_SERVER_IP,
        BACNET_SERVER_PORT,
        BACNET_SERVER_DEVICEID,
    )

    for data, (subscription, pv) in zip(test_data, subscriptions.items(), strict=True):
        if subscription.object_id.object_type == "analog-output":
            device.create_analog_output_object(
                pv, "Placeholder Description", ConstantVariable(pv, data.expected_value)
            )

    yield device

    await device.disconnect()


@pytest.fixture
async def fastcs_application(
    subscriptions: dict[SubscriptionID, str],
) -> AsyncGenerator[None]:
    """The main application under test"""
    task = asyncio.create_task(fastcs_bacnet(subscriptions))
    yield
    task.cancel()
    await task


async def test_experiments(
    test_data: list[ObjectData],
    subscriptions: dict[SubscriptionID, str],
    bacnet_server,
    fastcs_application,
):

    for data, pv in zip(test_data, subscriptions.values(), strict=True):
        val = await aioca.caget(f"FASTCS_BACNET:Subcontroller0:{pv}")
        assert val == data.expected_value
