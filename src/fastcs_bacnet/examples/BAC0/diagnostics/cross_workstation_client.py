import asyncio
from datetime import datetime as dt

from BAC0 import start
from bacpypes3.primitivedata import PropertyIdentifier

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

    output_file = open("./recieved_BAC0_updates.txt", "w")

    def default_generic_callback(
        subscription_id: SubscriptionID,
        property_identifier: str,
        property_value: float,
    ):
        if property_identifier == PropertyIdentifier.presentValue:
            output_file.write(
                f"DATA: {subscription_id.address}:{subscription_id.port}"
                + f",{subscription_id.object_id}.\n"
            )

    bac0_client = start()

    start_time = dt.now()

    BacnetClient(
        bacnet_client=bac0_client,
        initial_subscriptions=initial_subscriptions,
        default_generic_callback=default_generic_callback,
        auto_renew_subscriptions=False,
        subscription_lifetime=70,
    )

    await asyncio.sleep(20)

    end_time = dt.now()
    print("DISCONNECTING")
    print("time: ", end_time)

    await bac0_client.disconnect()

    output_file.write(f"TIMES// start_time: /{start_time}/, end_time: /{end_time}/\n")
    output_file.write("END\n")
    output_file.close()


asyncio.run(async_function())
