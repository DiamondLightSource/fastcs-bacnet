import asyncio
from dataclasses import dataclass

import BAC0
import pytest
from fastcs.logging import LogLevel, configure_logging, intercept_std_logger, logger

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

BACNET_SERVER_IP = "127.0.0.1"


@pytest.fixture(autouse=True)
def _logging():
    """Configure logging to redirect everything to loguru"""
    # TODO: Do we actually want to do this for our main application?
    BAC0.log_level(level="critical", log_this=False)
    configure_logging(LogLevel.CRITICAL)
    intercept_std_logger("BAC0_Root.BAC0.core.app.asyncApp.BAC0Application")
    intercept_std_logger("BAC0_Root.BAC0.scripts.Lite.Lite")
    intercept_std_logger("BAC0_Root.BAC0.tasks.RecurringTask.RecurringTask")
    intercept_std_logger("BAC0_Root.BAC0.core.devices.local.factory.ObjectFactory")
    intercept_std_logger("BAC0_Root.BAC0.tasks.TaskManager.Task")


@pytest.fixture
def loguru_caplog(caplog):
    """Make loguru's logging accessible to Pytest's caplog"""
    handler_id = logger.add(caplog.handler, format="{message}", level="DEBUG")
    yield caplog
    logger.remove(handler_id)


@dataclass
class ObjectData:
    """Describes a single Bacnet Object"""

    object_type: str
    object_instance: int
    expected_value: bool | float
    pv: str = ""


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


def create_bacnet_server(data: DeviceData):
    device = Device(data.device_ip, data.device_port, data.device_id)

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

        device.create_object(
            object.pv,
            "Placeholder Description",
            object.object_instance,
            ConstantVariable(object.pv, object.expected_value),
            creation_func,
        )

    return device


@pytest.fixture
async def bacnet_servers(device_data: list[DeviceData]):
    """Create and start bacnet servers"""

    devices = []

    for data in device_data:
        device = create_bacnet_server(data)
        devices.append(device)

    yield

    await asyncio.gather(*[device.disconnect() for device in devices])
