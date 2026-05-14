import asyncio
from collections.abc import Callable

from BAC0 import lite

from fastcs_bacnet.practical.BAC0.device_subscription import DeviceSubscription
from fastcs_bacnet.practical.BAC0.object_subscription import ObjectSubscription
from fastcs_bacnet.practical.BAC0.subscription_id import (
    IPv4SocketAddress,
    SubscriptionID,
)


class BacnetClient:
    """
    Creates and stores DeviceSubscription s

    Does NOT handle them
    """

    _devices: dict[IPv4SocketAddress, DeviceSubscription]
    _subscription_ids: set[SubscriptionID]
    _task_pool: set[asyncio.Task]

    def __init__(
        self,
        bacnet_client: lite,
        initial_subscriptions: list[SubscriptionID] | None = None,
        subscription_lifetime: int = 60,
    ):
        """
        bacnet_client: python bacnet object used to interact with actual bacnet objects
            can use this classes disconnect method to disconnect it
            or disconnect manually outside
        initial_subscriptions: A list of SubsciptionIDs the object can use
            to make subscriptions in the constructor
            Just loops through this list and calls add_subscription
        subscription_lifetime: Time that subscriptions last (in seconds)
            this will affect the amount of traffic on the network (a message
            must be sent to renew the subscription)
        """
        self._subscription_lifetime = subscription_lifetime

        self._bacnet_client = bacnet_client

        self._devices = {}
        self._subscription_ids = set()

        if initial_subscriptions is not None:
            for subscription_id in initial_subscriptions:
                task = asyncio.create_task(self.add_subscription(subscription_id))
                self._task_pool.add(task)
                task.add_done_callback(self._task_pool.discard)

    async def add_subscription(
        self,
        subscription_id: SubscriptionID,
        callback: Callable[[str, float], None] | None = None,
    ):
        """
        Adds a new subscription object to the dictionary
        subscription_id: identifier used to find the object to subscribe to
        callback: Procedure that is called when a new value is recieved from the device
            If None no callback function will be used
        """

        if subscription_id.socket_address not in self._devices:
            self._devices[subscription_id.socket_address] = DeviceSubscription(
                self._bacnet_client, subscription_id.socket_address
            )

        await self._devices[subscription_id.socket_address].add_subscription(
            subscription_id.object_key,
            self._subscription_lifetime,
            callback=callback,
        )

        self._subscription_ids.add(subscription_id)

    def remove_subscription(self, subscription_id: SubscriptionID):
        """
        Removes a subscription from the dictionary
        subscription_id: identifier used to find the object to subscribe to
        """
        if subscription_id.socket_address not in self._devices:
            print("raise error here")

        self._devices[subscription_id.socket_address].remove_subscription(
            subscription_id.object_key
        )

    def get_subscription(
        self, subscription_id: SubscriptionID
    ) -> ObjectSubscription | None:
        if subscription_id.socket_address not in self._devices:
            print("raise error here")
            return None

        return self._devices[subscription_id.socket_address].get_subscription(
            subscription_id.object_key
        )

    def get_subscription_ids(self) -> set[SubscriptionID]:
        return self._subscription_ids
