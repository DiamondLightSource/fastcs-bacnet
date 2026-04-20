import socket

from BAC0 import start

from conftest import get_multiprocessing_context
from fastcs_bacnet.dummy.BAC0.device import Device
from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)
from fastcs_bacnet.practical.FastCS.bacnet_controller import BacnetController


def start_dummy_device(pipe_context):
    device = Device(998, number_of_random_fields=1)
    device_object = device.get_object_from_name("random_object_0")

    def value_change_callback(new_value: float, old_value: float | None):
        pipe_context.send(new_value)

    device_object.device_variable.callback_stack.add_to_stack(value_change_callback)


def start_fastcs_bacnet(subscription_list: list[SubscriptionID]):
    bac0_instance = start()

    bacnet_client = BacnetClient(bac0_instance, initial_subscriptions=subscription_list)

    BacnetController(bacnet_client)


def start_epics_ca_process(pipe_context):

    # start ca process

    update_sent = pipe_context.recv()  # noqa: F841

    # compare update sent to ca result
    # some waits or syncs or something idk


def test_system():
    context = get_multiprocessing_context()

    parent_context, child_context = context.Pipe()

    dummy_device_process = context.Process(
        target=start_dummy_device, args=[child_context]
    )

    device_address = IPv4SocketAddress(
        socket.gethostbyname(socket.gethostname()), 47808
    )
    object_key = ObjectIdentifier("analog-output", 0)
    subscription_list = [SubscriptionID(device_address, object_key)]

    fastcs_bacnet_process = context.Process(
        target=start_fastcs_bacnet, args=[subscription_list]
    )

    epics_ca_process = context.Process(
        target=start_epics_ca_process, args=[parent_context]
    )

    dummy_device_process.start()
    fastcs_bacnet_process.start()
    epics_ca_process.start()

    # Do we need clean up for tests??
