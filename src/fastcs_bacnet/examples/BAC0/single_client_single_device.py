import asyncio
from datetime import datetime as dt

from BAC0 import start
from bacpypes3.primitivedata import PropertyIdentifier

from fastcs_bacnet.dummy.BAC0.device import Device
from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)

IP_ADDRESS = "127.0.0.1"
DUMMY_DEVICE_PORT = 47810
DUMMY_DEVICE_ID = 123


async def asyc_function():

    ### Create dummy bacnet devices (setting up environment) ###
    Device(
        IP_ADDRESS,
        DUMMY_DEVICE_PORT,
        DUMMY_DEVICE_ID,
        number_of_oscillating_fields=1,
    )

    ### Create bacnet client device ###
    bac0_client = start(ip=IP_ADDRESS, port=47808, deviceId=0)

    bacnet_client = BacnetClient(
        bac0_client,
        initial_subscriptions=[],
    )

    ### Subscription argument set up ###
    # Locate device using address and port
    # Specify object to subscribe to ("analog-output" instance 0)
    # All dummy device objects are CURRENTLY analog-output s
    dummy_device_subscription = SubscriptionID(
        IPv4SocketAddress(IP_ADDRESS, DUMMY_DEVICE_PORT),
        ObjectIdentifier("analog-output", 0),
    )

    # Function that runs when any object value is changed
    # This is usually where you would update local state, this one just prints data
    def callback(property_identifier: str, property_value: float):
        # we only care about the actual value of the object

        # NOTE: The typing of callback is technically ?wrong? in BAC0 and my code
        # property_identifier is an enum (PropertyIdentifier)
        # where the values are integers
        if property_identifier == PropertyIdentifier.presentValue:
            time = dt.now()
            print(f"""
                Value changed!
                Time: {time}
                Location: {dummy_device_subscription.socket_address.ip_address} :
                {dummy_device_subscription.socket_address.port}
                Object type: {dummy_device_subscription.object_key.object_type}
                Object id number: {dummy_device_subscription.object_key.object_instance}
                Property Identifier: {property_identifier}
                New value: {property_value}
            """)

    ### Actually adds (and starts) the subscription ###
    bacnet_client.add_subscription(dummy_device_subscription, callback=callback)

    ### Keep async thread alive ###
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(asyc_function())
