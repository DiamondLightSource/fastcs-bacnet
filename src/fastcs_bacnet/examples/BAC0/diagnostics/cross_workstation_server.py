import asyncio

from fastcs_bacnet.dummy.BAC0.device import Device

DUMMY_DEVICE_PORTS = []
DUMMY_DEVICE_IDS = []
NUMBER_OF_FIELDS = 0


async def async_function():
    dummy_devices = []

    for i in range(len(DUMMY_DEVICE_PORTS)):
        port = DUMMY_DEVICE_PORTS[i]
        id = DUMMY_DEVICE_IDS[i]

        dummy_device = Device(None, port, id, number_of_random_fields=NUMBER_OF_FIELDS)
        dummy_devices.append(dummy_device)

    await asyncio.Event().wait()

    for dummy_device in dummy_devices:
        await dummy_device.disconnect()


asyncio.run(async_function())
