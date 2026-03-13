import asyncio

import BAC0

from fastcs_bacnet.dummy_bacnet_object import DummyOscillatingObject


def get_object_values():
    asyncio.run(_a_get_object_values())


async def _a_get_object_values():
    address = "127.0.0.1"
    bacnet_port = 47808
    dummy_device_1_port = 47809
    bacnet_device_id = 123
    dummy_device_1_id = 121

    bac0_devices: list[BAC0.start] = []

    bacnet = BAC0.start(ip=address, port=bacnet_port, deviceId=bacnet_device_id)
    bac0_devices.append(bacnet)
    dummy_device_1 = BAC0.start(
        ip=address, port=dummy_device_1_port, deviceId=dummy_device_1_id
    )
    bac0_devices.append(dummy_device_1)

    try:
        DummyOscillatingObject(
            dummy_device_1, "OS1", "Dummy Oscillating Object 1", debug=True
        )

        # 2 ways of doing this: from a controller or directly from the client
        # TODO: Make these cli arguments
        use_controller = False
        query_time = 1.1

        if use_controller:
            # make a device controller
            # this is one option for interfacing with devices over the network
            # (but has some wierd quirks)
            device_controller = await BAC0.device(
                f"{address}:{dummy_device_1_port}", dummy_device_1_id, bacnet
            )

            while True:
                # very simple to get object values using a controller
                # WARNING: there seems to be a strange bug where sometimes the value
                # just doesnt update?? Better off using the network client directly
                os1_value = await device_controller["OS1"].value
                print("OS1 value recorded from controller: ", os1_value)
                await asyncio.sleep(query_time)

        else:
            while True:
                # have to pass a single string argument to bacnet.read
                # this includes 4 arguments separated by commas
                # 1: address (IP and port when using differing ports)
                # 2: Output type
                # WARNING: this seems to be quite incosistant, sometimes camel case
                # sometimes kebab case, if in doubt check for a dummy device
                # using device["object name"].__dict__
                # 3: Object ID? I think this just increments starting at 0??
                # 4: Object property, presentValue is most useful
                read_argument = (
                    f"{address}:{dummy_device_1_port} analog-output 0 presentValue"
                )
                os1_value = await bacnet.read(read_argument)
                print("OS1 value recorded from client read: ", os1_value)
                await asyncio.sleep(query_time)

    finally:
        for device in bac0_devices:
            await device.disconnect()
