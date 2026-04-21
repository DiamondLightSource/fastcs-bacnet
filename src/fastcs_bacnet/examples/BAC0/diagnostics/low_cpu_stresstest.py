import asyncio
from datetime import timedelta

from BAC0 import start

from fastcs_bacnet.diagnostics.BAC0.response_timer import ResponseTimer
from fastcs_bacnet.dummy.BAC0.device import Device
from fastcs_bacnet.dummy.generic.device_variables.puppet_variable.puppet_controller import (  # noqa: E501
    PuppetController,
)
from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)

IP_ADDRESS = "127.0.0.1"
DUMMY_DEVICE_STARTING_PORT = 47810
DUMMY_DEVICE_STARTING_ID = 123


async def get_subscription_data(
    number_of_devices: int,
    fields: int,
    min_change_time: float,
    max_change_time: float,
    sample_time: int = 60,
) -> timedelta:

    dummy_devices: dict[IPv4SocketAddress, Device] = {}
    subscription_ids = []

    puppet_controller = PuppetController(
        [], min_change_time=min_change_time, max_change_time=max_change_time
    )

    for i in range(number_of_devices):
        port = DUMMY_DEVICE_STARTING_PORT + i
        device_id = DUMMY_DEVICE_STARTING_ID + i
        socket_address = IPv4SocketAddress(IP_ADDRESS, port)

        dummy_device = Device(
            IP_ADDRESS,
            port,
            device_id,
            number_of_puppet_fields=fields,
            puppet_controller=puppet_controller,
        )
        dummy_devices[socket_address] = dummy_device

        subscription_ids += [
            SubscriptionID(
                IPv4SocketAddress(IP_ADDRESS, port),
                ObjectIdentifier("analog-output", i),
            )
            for i in range(fields)
        ]

    bac0_object = start()
    bacnet_client = BacnetClient(
        bac0_object,
        initial_subscriptions=subscription_ids,
        subscription_lifetime=sample_time + 5,
        auto_renew_subscriptions=False,
    )

    response_timer = ResponseTimer(
        recent_times_buffer_length=int(sample_time / min_change_time)
    )

    for subscription_id in bacnet_client.get_subscription_ids():
        # quite a hacky way of doing it
        # I've made things difficult for myself by giving device objects names
        device_object = dummy_devices[
            subscription_id.socket_address
        ].get_object_from_name(
            "puppet_object_" + str(subscription_id.object_key.object_instance)
        )
        object_subscription = bacnet_client.get_subscription(subscription_id)
        response_timer.add_subscription_pair(device_object, object_subscription)

    puppet_controller.start_update_loops()
    print("sampling")
    await asyncio.sleep(sample_time)
    print("sampling done")
    print("average response time: ", response_timer.get_average_response_time())
    print("reliability score: ", response_timer.get_average_reliability())

    await bacnet_client.disconnect()
    for device_key in dummy_devices.keys():
        await dummy_devices[device_key].disconnect()

    return response_timer.get_average_response_time()


print(
    asyncio.run(
        get_subscription_data(
            10, 2, min_change_time=1.0, max_change_time=5.0, sample_time=30
        )
    )
)
