import asyncio

import BAC0

from fastcs_bacnet.dummy_bacnet_object import (
    DummyConstantObject,
    DummyOscillatingObject,
    DummyRandomChangeObject,
)


def dummy_devices_with_objects():
    asyncio.run(_a_dummy_devices_with_objects())


# has to be an async function to run awaits
async def _a_dummy_devices_with_objects():
    address = "127.0.0.1"
    # since were using one IP address we need to use
    # different ports for different devices
    bacnet_port = 47808
    dummy_device_1_port = 47809
    dummy_device_2_port = 47810
    bacnet_device_id = 123
    dummy_device_1_id = 121
    dummy_device_2_id = 114

    # a list of all dummy devices makes it easier to clean up later
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
        # I made classes to add objects to devices because I didnt like the way
        # BAC0 does it
        # Give the device you want to connect it to as an argument, then the object
        # name and description. Specific objects that are supposed to mimic real data
        # have some other parameters
        # It doesnt  replicate all the features of the original factory functions
        # but its good enough to generate test data
        DummyConstantObject(dummy_device_1, "CO1", "Dummy Constant Object 1", 10.0)

        # Oscialating objects constantly change their values in a sinosodial pattern
        # Amplitude, frequency and offset (y modification) of the wave can be specified
        # refresh rate is how frequently the object changes its value
        # The debug option can be used to output the new value every time it changes
        DummyOscillatingObject(
            dummy_device_1, "OS1", "Dummy Oscillating Object 1", instance=1
        )
        DummyOscillatingObject(
            dummy_device_2,
            "OS2",
            "Dummy Oscillating Object 2",
            amplitude=5.0,
            offset=2.0,
            frequency=0.3,
            refresh_rate=0.7,
            debug=True,
        )
        # ALSO worth noting that you have to specify an instance number if multiple
        # objects are added to a device, they must be unique
        # technically the object type and instance pair have to be unique per device

        # Random change objects change to a random value in a uniform distribution
        # between min_value and max_value at a random time interval (also a
        # uniform distribution) between min_change_time and max_change_time
        DummyRandomChangeObject(
            dummy_device_2, "RN1", "Dummy Random Object 1", instance=1
        )
        DummyRandomChangeObject(
            dummy_device_2,
            "RN2",
            "Dummy Random Object 2",
            min_change_time=1.0,
            max_change_time=1.5,
            min_value=1.0,
            max_value=5.0,
            instance=2,
            debug=True,
        )

        await asyncio.sleep(20)

    # Cleans up all devices even if main code errors
    # If you put async code in an object deconstructor (I did originally)
    # there is no guarantee of it running
    finally:
        for device in bac0_devices:
            await device.disconnect()
