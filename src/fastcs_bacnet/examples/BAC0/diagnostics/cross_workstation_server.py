import asyncio

from fastcs_bacnet.dummy.BAC0.device import Device

DUMMY_DEVICE_PORT = 47808
DUMMY_DEVICE_ID = 125


async def async_function():

    dummy_device_0 = Device(
        None,
        DUMMY_DEVICE_PORT,
        DUMMY_DEVICE_ID,
        number_of_constant_fields=20,
    )

    input()

    await dummy_device_0.disconnect()


asyncio.run(async_function())
