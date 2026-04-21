import asyncio

from BAC0 import start

from fastcs_bacnet.dummy.BAC0.device import Device
from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscriptions.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)

IP_ADDRESS = "127.0.0.1"
DUMMY_DEVICE_PORTS = [47900, 47970, 47985]
DUMMY_DEVICE_IDS = [543, 78, 34]


async def asyc_function():

    ### Create dummy bacnet devices (setting up environment) ###
    Device(
        IP_ADDRESS,
        DUMMY_DEVICE_PORTS[0],
        DUMMY_DEVICE_IDS[0],
        number_of_constant_fields=5,
    )
    Device(
        IP_ADDRESS,
        DUMMY_DEVICE_PORTS[1],
        DUMMY_DEVICE_IDS[1],
        number_of_oscillating_fields=5,
    )
    named_dummy_device = Device(
        IP_ADDRESS,
        DUMMY_DEVICE_PORTS[2],
        DUMMY_DEVICE_IDS[2],
        number_of_oscillating_fields=6,
        number_of_random_fields=7,
    )

    ### Subscriptions argument set up ###
    # Specify objects to subscribe to for bacnet client
    subscription_ids = [
        # how you would have to specify objects on a real network
        SubscriptionID(
            IPv4SocketAddress(IP_ADDRESS, DUMMY_DEVICE_PORTS[0]),
            ObjectIdentifier("analog-output", 4),
        ),
        SubscriptionID(
            IPv4SocketAddress(IP_ADDRESS, DUMMY_DEVICE_PORTS[1]),
            ObjectIdentifier("analog-output", 1),
        ),
        # for dummy bacnet objects we can use names
        SubscriptionID(
            IPv4SocketAddress(IP_ADDRESS, DUMMY_DEVICE_PORTS[2]),
            ObjectIdentifier(
                named_dummy_device.object_identifier_from_name("random_object_4")[0],
                named_dummy_device.object_identifier_from_name("random_object_4")[1],
            ),
        ),
    ]

    ### Create bacnet client device ###
    bac0_client = start(ip=IP_ADDRESS, port=47808, deviceId=0)

    BacnetClient(
        bac0_client,
        initial_subscriptions=subscription_ids,
    )

    # TODO: add callbacks to all the subscriptions here

    ### Keep async thread alive ###
    while True:
        await asyncio.sleep(10)


asyncio.run(asyc_function())
