import asyncio
from datetime import timedelta

from fastcs_bacnet.diagnostics.BAC0.response_timer import ResponseTimer
from fastcs_bacnet.dummy.BAC0.device import Device
from fastcs_bacnet.dummy.generic.device_variables.puppet_variable.puppet_controller import (  # noqa: E501
    PuppetController,
)
from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID

ip_address = "127.0.0.1"
dummy_device_starting_port = 47810
dummy_device_starting_id = 123


async def get_subscription_data(
    number_of_devices: int,
    fields: int,
    min_change_time: float,
    max_change_time: float,
    sample_time: int = 60,
) -> timedelta:

    dummy_devices: dict[int, Device] = {}
    subscription_ids = []

    puppet_controller = PuppetController(
        [], min_change_time=min_change_time, max_change_time=max_change_time
    )

    for i in range(number_of_devices):
        port = dummy_device_starting_port + i
        device_id = dummy_device_starting_id + i
        dummy_device = Device(
            ip_address,
            port,
            device_id,
            number_of_puppet_fields=fields,
            puppet_controller=puppet_controller,
        )
        dummy_devices[port] = dummy_device

        subscription_ids += [
            SubscriptionID(ip_address, port, "analog-output", i) for i in range(fields)
        ]

    bacnet_client = BacnetClient(
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
        device_object = dummy_devices[subscription_id.port].get_object_from_name(
            "puppet_object_" + str(subscription_id.object_id)
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
