"""Interface for ``python -m fastcs_bacnet``."""

import asyncio
from argparse import ArgumentParser
from collections.abc import Sequence

import BAC0
from BAC0.core.devices.local.factory import (
    analog_input,
    binary_output,
)

from . import __version__

__all__ = ["main"]


def main(args: Sequence[str] | None = None) -> None:
    """Argument parser for the CLI."""
    parser = ArgumentParser()
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=__version__,
    )
    parser.parse_args(args)
    print("hello world!!")
    asyncio.run(start_bacnet())


async def start_bacnet():
    address = "127.0.0.1"
    bacnet_port = 47808
    dummy_device_1_port = 47809
    dummy_device_2_port = 47810
    bacnet_device_id = 123
    dummy_device_1_id = 121
    dummy_device_2_id = 114

    bac0_devices: list[BAC0.start] = []

    # creates bacnet client device and 2 dummy devices
    # uses different ports for dummy devices instead of different IPs so it can all run
    # locally
    bacnet = BAC0.start(ip=address, port=bacnet_port, deviceId=bacnet_device_id)
    bac0_devices.append(bacnet)
    dummy_device_1 = BAC0.start(
        ip=address, port=dummy_device_1_port, deviceId=dummy_device_1_id
    )
    bac0_devices.append(dummy_device_1)
    dummy_device_2 = BAC0.start(
        ip=address, port=dummy_device_2_port, deviceId=dummy_device_2_id
    )
    bac0_devices.append(dummy_device_2)

    try:
        # uses imported factory functions to create BACnet objects
        # these objects are stored in the theoretical "accumulator"
        ref = analog_input(
            name="TW1",
            description="Water temperature 1",
            properties={"units": "degreesCelsius"},
        )
        binary_output(
            name="Night",
            description="Day/Night flag",
            properties={"inactiveText": "day", "activeText": "night"},
        )

        # we are never given a reference to the accumulator but its methods are attached
        #   to all BACnet objects
        # adds all objects from the accumulator to dummy device 1
        ref.add_objects_to_application(dummy_device_1)
        # clears the accumulator
        # otherwise the last 2 objects would be added to another device next time we
        #   called add_objects_to_application
        ref.clear_objects()

        ref = analog_input(
            name="TW1",
            description="Water temperature 1",
            properties={"units": "degreesCelsius"},
            presentValue=1,
        )
        binary_output(
            name="Night2",
            description="Day/Night flag",
            properties={"inactiveText": "day", "activeText": "night"},
        )
        ref.add_objects_to_application(dummy_device_2)
        ref.clear_objects()

        # sets values of device objects
        # we could have done this in the factory functions if we wanted
        # PyLance REALLY doesnt like this dynamic typing trick
        dummy_device_1["TW1"].presentValue = 21.5  # type: ignore
        dummy_device_1["Night"].presentValue = False  # type: ignore

        dummy_device_2["TW1"].presentValue = 11.5  # type: ignore
        dummy_device_2["Night2"].presentValue = True  # type: ignore

        # makes controllers for each dummy device using bacnet client device
        # controllers are essentially just references to devices (different classes are
        #   used though)
        dummy_device_1_controller = await BAC0.device(f"{address}:47809", 121, bacnet)
        # prints all objects of a device
        # objects are called points when referenced from a device
        print(
            "device 1 points: ",
            dummy_device_1_controller.points,
        )
        # This is how we get object values using a device
        value = await dummy_device_1_controller["TW1"].value
        print("value: ", value)

        dummy_device_2_controller = await BAC0.device(f"{address}:47810", 114, bacnet)
        print(
            "device 2 points: ",
            dummy_device_2_controller.points,
        )
        value2 = await dummy_device_2_controller["TW1"].value
        print("value: ", value2)

    finally:
        # need to disconnect all devices when finished
        # dont need to do the same for controllers?
        # Usually you use a context manager but with more devices that causes so much
        #   indentation
        for device in bac0_devices:
            await device.disconnect()


if __name__ == "__main__":
    main()
