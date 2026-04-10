import asyncio
from datetime import timedelta

from fastcs_bacnet.diagnostics.BAC0.response_timer import ResponseTimer
from fastcs_bacnet.dummy.BAC0.device import Device
from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID

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

    dummy_devices = {}
    subscription_ids = []

    for i in range(number_of_devices):
        port = DUMMY_DEVICE_STARTING_PORT + i
        device_id = DUMMY_DEVICE_STARTING_ID + i
        dummy_device = Device(
            IP_ADDRESS,
            port,
            device_id,
            number_of_random_fields=fields,
            min_change_time=min_change_time,
            max_change_time=max_change_time,
        )
        dummy_devices[port] = dummy_device

        subscription_ids += [
            SubscriptionID(IP_ADDRESS, port, "analog-output", i) for i in range(fields)
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


print(
    asyncio.run(
        get_subscription_data(
            100, 10, min_change_time=1.0, max_change_time=5.0, sample_time=300
        )
    )
)
