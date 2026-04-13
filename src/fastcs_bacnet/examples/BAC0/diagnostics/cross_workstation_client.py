import asyncio

from BAC0 import start

CLIENT_PORT = 47808
CLIENT_ID = 145

DUMMY_PORT = 47808
DUMMY_IP = "..."


async def async_function():

    bac0_client = start(port=CLIENT_PORT, deviceId=CLIENT_ID)

    read_argument = f"{DUMMY_IP}:{DUMMY_PORT} analog-output 0 presentValue"
    os1_value = await bac0_client.read(read_argument)
    print("value recorded from client read: ", os1_value)

    await bac0_client.disconnect()


asyncio.run(async_function())
