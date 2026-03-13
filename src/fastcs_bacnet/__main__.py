"""Interface for ``python -m fastcs_bacnet``."""

import asyncio
from argparse import ArgumentParser
from collections.abc import Sequence

import BAC0

from fastcs_bacnet.dummy_bacnet_object import (
    DummyRandomChangeObject,
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
        DummyRandomChangeObject(dummy_device_1, "OB1", "Dummy Object 1")

        def callback(property_identifier, property_value, **_):
            print(property_identifier, ": ", property_value)

        use_controller = True

        # two methods of starting a change of value subscription
        # one with a controller and one without
        # sometimes they miss a change if it happens too quickly??
        if use_controller:
            dummy_device_1_controller = await BAC0.device(
                f"{address}:{dummy_device_1_port}", dummy_device_1_id, bacnet
            )

            await dummy_device_1_controller["OB1"].subscribe_cov(
                lifetime=1000, callback=callback
            )
        else:
            bacnet.cov(
                f"{address}:{dummy_device_1_port}",
                ("analog-output", 0),
                lifetime=1000,
                callback=callback,
            )

        await asyncio.sleep(5)

    finally:
        for device in bac0_devices:
            await device.disconnect()


if __name__ == "__main__":
    main()
