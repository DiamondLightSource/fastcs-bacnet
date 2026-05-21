import asyncio

from BAC0 import lite

from fastcs_bacnet.core.BAC0.callback_holder import CovCallback
from fastcs_bacnet.core.BAC0.device_subscription import DeviceSubscription
from fastcs_bacnet.core.BAC0.object_subscription import ObjectSubscription
from fastcs_bacnet.core.BAC0.subscription_id import (
    IPv4SocketAddress,
    SubscriptionID,
)


class BacnetClient:
    """
    Creates and stores DeviceSubscription s for given SubscriptionIDs

    Does NOT handle them
    """

    _devices: dict[IPv4SocketAddress, DeviceSubscription]
    _task_pool: set[asyncio.Task]

    def __init__(
        self,
        bacnet_client: lite,
        initial_subscriptions: list[SubscriptionID] | None = None,
        subscription_lifetime: int = 3600,
    ):
        """
        bacnet_client: BAC0 object used to interact with actual bacnet objects
        initial_subscriptions: The subscriptions that are created on construction
            Subscriptions are NOT automatically started after being created,
            a start_subscriptions() call must be made
        subscription_lifetime: Time that subscriptions last (in seconds)
            This WILL affect the amount of traffic on the network (a message
           must be sent to renew the subscription) and so should be set to 1+ hours
        """
        self._subscription_lifetime = subscription_lifetime

        self._bacnet_client = bacnet_client

        self._devices = {}

        if initial_subscriptions is not None:
            for subscription_id in initial_subscriptions:
                task = asyncio.create_task(self.add_subscription(subscription_id))
                self._task_pool.add(task)
                task.add_done_callback(self._task_pool.discard)

    async def add_subscriptions(self, subscription_ids: list[SubscriptionID]):
        """
        Adds a list of subscriptions at one time

        Faster than adding them one by one and waiting after each
        Better than creating a task for each add_subscription because
        you can know when it finishes

        subscription_ids: Subscriptions to add
        """

        async with asyncio.TaskGroup() as task_group:
            for subscription_id in subscription_ids:
                task_group.create_task(self.add_subscription(subscription_id))

    async def add_subscription(
        self,
        subscription_id: SubscriptionID,
        callback: CovCallback | None = None,
    ):
        """
        Creates a subscription to a device on an object

        subscription_id: Identifier used to find the object to subscribe to
        callback: Procedure that is called when a change of value (CoV) update is
            received from the device
            Parameters are property_type and property_value
            If None no callback function will be used
        """

        if subscription_id.socket_address not in self._devices:
            self._devices[subscription_id.socket_address] = DeviceSubscription(
                self._bacnet_client, subscription_id.socket_address
            )

        await self._devices[subscription_id.socket_address].add_subscription(
            subscription_id.object_id,
            self._subscription_lifetime,
            callback=callback,
        )

    def get_subscription(self, subscription_id: SubscriptionID) -> ObjectSubscription:
        if subscription_id.socket_address not in self._devices:
            raise KeyError(
                "No subscription in BacnetClient to device "
                + str(subscription_id.socket_address)
            )

        return self._devices[subscription_id.socket_address].get_subscription(
            subscription_id.object_id
        )

    def get_subscription_ids(self) -> set[SubscriptionID]:
        subscription_ids: set[SubscriptionID] = set()
        for device in self._devices.values():
            subscription_ids = subscription_ids | device.get_subscription_ids()

        return subscription_ids

    async def start_subscriptions(self):
        for device in self._devices.values():
            await device.start_subscriptions()
