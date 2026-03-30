import asyncio
from datetime import datetime as dt

from BAC0 import start
from bacpypes3.primitivedata import PropertyIdentifier

from fastcs_bacnet.dummy.BAC0.device import Device
from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID

ip_address = "127.0.0.1"
dummy_device_ports = [47900, 47970, 47985]
dummy_device_ids = [543, 78, 34]


async def asyc_function():

    ### Create dummy bacnet devices (setting up environment) ###
    Device(
        ip_address,
        dummy_device_ports[0],
        dummy_device_ids[0],
        number_of_constant_fields=5,
    )
    Device(
        ip_address,
        dummy_device_ports[1],
        dummy_device_ids[1],
        number_of_oscillating_fields=5,
    )
    named_dummy_device = Device(
        ip_address,
        dummy_device_ports[2],
        dummy_device_ids[2],
        number_of_oscillating_fields=6,
        number_of_random_fields=7,
    )

    ### Subscriptions argument set up ###
    # Specify objects to subscribe to for bacnet client
    subscription_ids = [
        # how you would have to specify objects on a real network
        SubscriptionID(ip_address, dummy_device_ports[0], "analog-output", 4),
        SubscriptionID(ip_address, dummy_device_ports[1], "analog-output", 1),
        # for dummy bacnet objects we can use names
        SubscriptionID(
            ip_address,
            dummy_device_ports[2],
            named_dummy_device.object_identifier_from_name("random_object_4")[0],
            named_dummy_device.object_identifier_from_name("random_object_4")[1],
        ),
    ]

    # OPTIONAL: specify a generic callback
    def generic_callback(
        subscription_id: SubscriptionID,
        property_identifier: str,
        property_value: float,
    ):
        if property_identifier == PropertyIdentifier.presentValue:
            time = dt.now()
            print(f"""
                Value changed!
                Time: {time}
                Location: {subscription_id.address} : {subscription_id.port}
                Object type: {subscription_id.object_type}
                Object id number: {subscription_id.object_id}
                Property Identifier: {property_identifier}
                New value: {property_value}
            """)

    ### Create bacnet client device ###
    bac0_client = start(ip=ip_address, port=47808, deviceId=0)

    BacnetClient(
        bac0_client,
        initial_subscriptions=subscription_ids,
        default_generic_callback=generic_callback,
    )

    ### Keep async thread alive ###
    while True:
        await asyncio.sleep(10)


asyncio.run(asyc_function())
