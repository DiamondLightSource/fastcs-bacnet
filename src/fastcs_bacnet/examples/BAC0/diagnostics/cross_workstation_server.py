import asyncio

from fastcs_bacnet.dummy.BAC0.device import Device

DUMMY_DEVICE_PORT = 47808
DUMMY_DEVICE_ID = 125


async def async_function():

    dummy_device_0 = Device(None, 47808, 998, number_of_constant_fields=10)

    await asyncio.Event().wait()

    await dummy_device_0.disconnect()


asyncio.run(async_function())
