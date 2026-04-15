import asyncio

from BAC0 import start

from fastcs_bacnet.practical.BAC0.object_subscription import SubscriptionID

CLIENT_PORT = 47808
CLIENT_ID = 145

DUMMY_PORT = 47808
DUMMY_IP = "172.23.245.103"


def create_subscription_id_list(
    ips: list[str], ports: list[int], object_instance_numbers: list[int]
) -> list[SubscriptionID]:
    subscription_id_list = []

    for ip in ips:
        for port in ports:
            for object_instance_number in object_instance_numbers:
                subscription_id_list.append(
                    SubscriptionID(ip, port, "analog-output", object_instance_number)
                )
    return subscription_id_list


async def async_function():

    bac0_client = start(port=CLIENT_PORT, deviceId=CLIENT_ID)

    read_argument = f"{DUMMY_IP}:{DUMMY_PORT} analog-output 0 presentValue"
    os1_value = await bac0_client.read(read_argument)
    print("value recorded from client read: ", os1_value)

    await bac0_client.disconnect()


asyncio.run(async_function())
