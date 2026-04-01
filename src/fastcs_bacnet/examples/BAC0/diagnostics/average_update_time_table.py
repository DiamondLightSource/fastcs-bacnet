import asyncio
from datetime import timedelta

from fastcs_bacnet.diagnostics.BAC0.response_timer import ResponseTimer
from fastcs_bacnet.dummy.BAC0.device import Device
from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID

ip_address = "127.0.0.1"
dummy_device_port = 47810
dummy_device_id = 123


async def get_subscription_data(
    fields: int, update_period: float, sample_time: int = 60
) -> timedelta:
    dummy_device = Device(
        ip_address,
        dummy_device_port,
        dummy_device_id,
        number_of_random_fields=fields,
        value_refresh_period=update_period,
    )

    subscription_ids: list[SubscriptionID] = [
        SubscriptionID(ip_address, dummy_device_port, "analog-output", i)
        for i in range(fields)
    ]

    bacnet_client = BacnetClient(
        initial_subscriptions=subscription_ids,
        subscription_lifetime=sample_time + 5,
        auto_renew_subscriptions=False,
    )

    response_timer = ResponseTimer(
        recent_times_buffer_length=int(sample_time / update_period)
    )

    for subscription_id in bacnet_client.get_subscription_ids():
        # quite a hacky way of doing it
        # I've made things difficult for myself by giving device objects names
        device_object = dummy_device.get_object_from_name(
            "random_object_" + str(subscription_id.object_id)
        )
        object_subscription = bacnet_client.get_subscription(subscription_id)
        response_timer.add_subscription_pair(device_object, object_subscription)

    print("sampling")
    await asyncio.sleep(sample_time)
    print("sampling done")
    print("average response time: ", response_timer.get_average_response_time())
    print("reliability score: ", response_timer.get_average_reliability())

    return response_timer.get_average_response_time()


print(asyncio.run(get_subscription_data(10, 2.0, sample_time=20)))
