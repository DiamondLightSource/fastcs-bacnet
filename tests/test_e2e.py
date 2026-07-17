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
from tests.dummy.BAC0.bacnet_object import (
    AnalogInputObject,
    AnalogOutputObject,
    AnalogValueObject,
    BacnetObject,
    BinaryInputObject,
    BinaryOutputObject,
    BinaryValueObject,
)
from tests.dummy.BAC0.device import Device
from tests.dummy.generic.device_variables.constant_variable import (
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
        ObjectData("analog-input", 0, 4.56, "abc-2"),
        ObjectData("analog-input", 1, 5.67, "ai-2"),
        ObjectData("analog-input", 2, 6.78, "analog-input-3"),
        ObjectData("analog-value", 0, 7.89, "abc-3"),
        ObjectData("analog-value", 1, 8.91, "av-2"),
        ObjectData("analog-value", 2, 9.10, "analog-value-3"),
        # Use "True" for all binary objects as the default is 0 aka False.
        ObjectData("binary-output", 0, True, "abc-4"),
        ObjectData("binary-output", 1, True, "bo-2"),
        ObjectData("binary-output", 2, True, "binary-output-3"),
        ObjectData("binary-input", 0, True, "abc-5"),
        ObjectData("binary-input", 1, True, "bi-2"),
        ObjectData("binary-input", 2, True, "binary-input-3"),
        ObjectData("binary-value", 0, True, "abc-6"),
        ObjectData("binary-value", 1, True, "bv-2"),
        ObjectData("binary-value", 2, True, "binary-value-3"),
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

    creation_func: type[BacnetObject]

    for data, (subscription, pv) in zip(test_data, subscriptions.items(), strict=True):
        match subscription.object_id.object_type:
            case "analog-output":
                creation_func = AnalogOutputObject
            case "analog-input":
                creation_func = AnalogInputObject
            case "analog-value":
                creation_func = AnalogValueObject
            case "binary-output":
                creation_func = BinaryOutputObject
            case "binary-input":
                creation_func = BinaryInputObject
            case "binary-value":
                creation_func = BinaryValueObject
            case _:
                pytest.fail(
                    f"Unrecognised object_type: {subscription.object_id.object_type}"
                )

        device.create_object(
            pv,
            "Placeholder Description",
            subscription.object_id.object_instance,
            ConstantVariable(pv, data.expected_value),
            creation_func,
        )

    yield device

    await device.disconnect()


@pytest.fixture
async def fastcs_application(
    subscriptions: dict[SubscriptionID, str],
) -> AsyncGenerator[None]:
    """The main application under test.

    Runs in a background task"""
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
