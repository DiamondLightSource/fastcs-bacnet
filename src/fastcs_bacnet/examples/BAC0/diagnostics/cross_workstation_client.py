import asyncio
from collections import defaultdict
from datetime import datetime as dt

from BAC0 import start

from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
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

    initial_subscriptions = create_subscription_id_list([], [], [])
    update_count = defaultdict(int)

    # open file

    def default_generic_callback(
        subscription_id: SubscriptionID,
        property_indentifier: str,
        property_value: float,
    ):
        if property_indentifier == "presentValue":
            # write ip, port and object instance number to file
            pass

        update_count[subscription_id.object_id] += 1

    bac0_client = start()

    start_time = dt.now()  # noqa: F841

    BacnetClient(
        bacnet_client=bac0_client,
        initial_subscriptions=initial_subscriptions,
        default_generic_callback=default_generic_callback,
        auto_renew_subscriptions=False,
        subscription_lifetime=70,
    )

    await asyncio.sleep(60)

    end_time = dt.now()
    print("DISCONNECTING")
    print("time: ", end_time)
    print("dict: ", update_count)

    await bac0_client.disconnect()

    # write times in file and close


asyncio.run(async_function())
