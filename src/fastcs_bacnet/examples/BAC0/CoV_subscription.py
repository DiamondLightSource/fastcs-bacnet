import asyncio

import BAC0

from fastcs_bacnet.dummy_bacnet_object import DummyRandomChangeObject


def cov_subscription():
    asyncio.run(_a_cov_subscription())


async def _a_cov_subscription():
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
        DummyRandomChangeObject(
            dummy_device_1, "OS1", "Dummy Oscillating Object 1", debug=True
        )

        def callback(property_identifier, property_value, **_):
            print(property_identifier, ": ", property_value)

        use_controller = True

        if use_controller:
            dummy_device_1_controller = await BAC0.device(
                f"{address}:{dummy_device_1_port}", dummy_device_1_id, bacnet
            )

            await dummy_device_1_controller["OB1"].subscribe_cov(
                lifetime=30, callback=callback
            )

        else:
            bacnet.cov(
                f"{address}:{dummy_device_1_port}",
                ("analog-output", 0),
                lifetime=30,
                callback=callback,
            )

        await asyncio.sleep(40)

    finally:
        for device in bac0_devices:
            await device.disconnect()
