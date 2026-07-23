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


@dataclass
class ObjectData:
    """Describes a single Bacnet Object"""

    object_type: str
    object_instance: int
    expected_value: bool | float
    pv = ""


@dataclass
class DeviceData:
    """Describes a Bacnet Device"""

    device_name: str
    device_ip: str
    device_port: int
    device_id: int
    object_data: list[ObjectData]


# A list of objects to add to each Bacnet server
bacnet_objects = [
    ObjectData("analog-output", 0, 1.23),
    ObjectData("analog-output", 1, 2.34),
    ObjectData("analog-output", 2, 3.45),
    ObjectData("analog-input", 0, 4.56),
    ObjectData("analog-input", 1, 5.67),
    ObjectData("analog-input", 2, 6.78),
    ObjectData("analog-value", 0, 7.89),
    ObjectData("analog-value", 1, 8.91),
    ObjectData("analog-value", 2, 9.10),
    # Use "True" for all binary objects as the default is 0 aka False.
    ObjectData("binary-output", 0, True),
    ObjectData("binary-output", 1, True),
    ObjectData("binary-output", 2, True),
    ObjectData("binary-input", 0, True),
    ObjectData("binary-input", 1, True),
    ObjectData("binary-input", 2, True),
    ObjectData("binary-value", 0, True),
    ObjectData("binary-value", 1, True),
    ObjectData("binary-value", 2, True),
]


@pytest.fixture
def device_data(unused_tcp_port_factory) -> list[DeviceData]:
    device_1 = DeviceData(
        "Device1", BACNET_SERVER_IP, unused_tcp_port_factory(), 5555, bacnet_objects
    )
    device_2 = DeviceData(
        "Device2", BACNET_SERVER_IP, unused_tcp_port_factory(), 5678, bacnet_objects
    )
    device_3 = DeviceData(
        "Device3", BACNET_SERVER_IP, unused_tcp_port_factory(), 8765, bacnet_objects
    )

    devices = [device_1, device_2, device_3]

    # Create PV name for each bacnet object
    for i, device in enumerate(devices):
        for object in device.object_data:
            object.pv = f"{i}:{object.object_type}-{object.object_instance}"

    return devices


@pytest.fixture
async def bacnet_servers(device_data: list[DeviceData]):
    """Create and start bacnet servers"""

    devices = []

    for data in device_data:
        device = Device(data.device_ip, data.device_port, data.device_id)
        devices.append(device)

        # for subscription, pv in subscriptions.items():
        for object in data.object_data:
            match object.object_type:
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
                    pytest.fail(f"Unrecognised object_type: {object.object_type}")
            print(f"Adding object {object}")
            device.create_object(
                object.pv,
                "Placeholder Description",
                object.object_instance,
                ConstantVariable(object.pv, object.expected_value),
                creation_func,
            )

    yield

    await asyncio.gather(*[device.disconnect() for device in devices])


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
