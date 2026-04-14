import asyncio

from BAC0 import start
from fastcs.launch import FastCS
from fastcs.transports.epics import EpicsIOCOptions
from fastcs.transports.epics.ca import EpicsCATransport

from fastcs_bacnet.dummy.BAC0.device import Device
from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)
from fastcs_bacnet.practical.FastCS.bacnet_controller import BacnetController

IP_ADDRESS = "127.0.0.1"
DUMMY_DEVICE_PORTS = [47900, 47970, 47985]
DUMMY_DEVICE_IDS = [543, 78, 34]


async def async_function():

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

    bacnet_client = start()

    bacnet_client = BacnetClient(
        bacnet_client,
        initial_subscriptions=subscription_ids,
    )

    epics_ca = EpicsCATransport(epicsca=EpicsIOCOptions(pv_prefix="DEMO"))
    controller = BacnetController(bacnet_client)

    fastcs = FastCS(controller, [epics_ca])

    asyncio.create_task(fastcs.serve())

    while True:
        await asyncio.sleep(10)


asyncio.run(async_function())

# NOTE: To acess variables through chanel access use command:
# caget DEMO:<subcontroller name>:<attribute name>
# ONLY SUBSCRIBED TO ATTRIBUTES WILL BE AVAILABLE
# caget DEMO:Subcontroller0:AnalogOutput4
# Subcontroller naming convention: Subcontroller<Instance Number>
# Attribute naming convention: AnalogOuput<Instance number>

# NOTE: All variables are currently analog outputs
# It is not possible to pick up the variable name from a device?
# You have to address them by variable type (analog-output) and instance number
# TODO: Add names susbcriptions. Can specify the attribute name for the object
