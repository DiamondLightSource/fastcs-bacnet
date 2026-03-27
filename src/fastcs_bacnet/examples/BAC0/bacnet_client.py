from BAC0 import start

from fastcs_bacnet.dummy.BAC0.device import Device
from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID

ip_address = "127.0.0.1"
dummy_device_ports = [47900, 47970, 47985]
dummy_device_ids = [543, 78, 34]

# Create dummy bacnet devices (setting up environment)
dummy_device_1 = Device(
    ip_address,
    dummy_device_ports[0],
    dummy_device_ids[0],
    number_of_constant_fields=500,
)
dummy_device_2 = Device(
    ip_address,
    dummy_device_ports[1],
    dummy_device_ids[1],
    number_of_oscillating_fields=500,
)
dummy_device_3 = Device(
    ip_address,
    dummy_device_ports[2],
    dummy_device_ids[2],
    number_of_oscillating_fields=600,
    number_of_random_fields=700,
)

# Specify objects to subscribe to for bacnet client
subscription_ids = [
    # how you would have to specify objects on a real network
    SubscriptionID(ip_address, dummy_device_ports[0], "analog-output", 23),
    SubscriptionID(ip_address, dummy_device_ports[0], "analog-output", 37),
    SubscriptionID(ip_address, dummy_device_ports[1], "analog-output", 12),
    SubscriptionID(ip_address, dummy_device_ports[1], "analog-output", 64),
    SubscriptionID(ip_address, dummy_device_ports[1], "analog-output", 335),
    SubscriptionID(ip_address, dummy_device_ports[2], "analog-output", 98),
    SubscriptionID(ip_address, dummy_device_ports[2], "analog-output", 214),
    # for dummy bacnet objects we can use names
    SubscriptionID(
        ip_address,
        dummy_device_ports[0],
        dummy_device_1.object_identifier_from_name("constant_object_45")[0],
        dummy_device_1.object_identifier_from_name("constant_object_45")[1],
    ),
    SubscriptionID(
        ip_address,
        dummy_device_ports[1],
        dummy_device_2.object_identifier_from_name("oscillating_object_283")[0],
        dummy_device_2.object_identifier_from_name("oscillating_object_283")[1],
    ),
    SubscriptionID(
        ip_address,
        dummy_device_ports[2],
        dummy_device_3.object_identifier_from_name("random_object_3")[0],
        dummy_device_3.object_identifier_from_name("random_object_3")[1],
    ),
]


# OPTIONAL: specify a generic callback
def generic_callback(
    subscription_id: SubscriptionID, property_indentifier: str, property_value: float
):
    print(f"""
          Value changed!
          Location: {subscription_id.address} : {subscription_id.port}
          Object type: {subscription_id.object_type}
          Object id number: {subscription_id.object_id}
          Property Identifier: {property_indentifier}
          New value: {property_value}
    """)


# Create bacnet client device
bac0_client = start(ip_address=ip_address, port=47808, device_id=0)
bacnet_client = BacnetClient(
    bac0_client,
    initial_subscriptions=subscription_ids,
    default_generic_callback=generic_callback,
)
