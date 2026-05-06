from asyncio import Lock
from collections.abc import Callable

from BAC0 import lite

from fastcs_bacnet.practical.BAC0.object_subscription import ObjectSubscription
from fastcs_bacnet.practical.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)


class SubscriptionLock(Lock):
    _acquired_by = ObjectIdentifier

    async def acquire_with(self, acquired_by: ObjectIdentifier):
        valid = await super().acquire()

        if valid:
            self._acquired_by = acquired_by

        return valid

    def release_with(self, released_by: ObjectIdentifier) -> bool:

        if released_by != self._acquired_by:
            return False
        super().release()
        return True


class DeviceSubscription:
    object_subscriptions: dict[ObjectIdentifier, ObjectSubscription]
    subscription_lock: SubscriptionLock
    down_subscriptions: set[ObjectSubscription]

    def __init__(self, ip_socket: IPv4SocketAddress):

        self.ip_socket = ip_socket
        self.object_subscriptions = {}
        self.subscription_lock = SubscriptionLock()
        self.down_subscriptions = set()

    async def add_subscription(
        self,
        bacnet_client: lite,
        object_id: ObjectIdentifier,
        lifetime: int,
        callback: Callable[[str, float], None] | None = None,
    ):

        await self.subscription_lock.acquire_with(object_id)

        def release(property_indentifier: str, property_value: float):
            if self.subscription_lock.locked():
                # Only releases if the object_key matches the one that locked it
                # This prevents other subscription notifications confirming a CoV
                self.subscription_lock.release_with(object_id)

        subscription_id = SubscriptionID(self.ip_socket, object_id)
        # object_subscription has to be set AFTER its created
        # This is because the callback must be defined before its created
        # We cant give the ObjectSubscription in the callback
        # because we would have to type this inside the ObjectSubscription class
        object_subscription: ObjectSubscription | None = None

        def failed_subscription_callback(_):
            if object_subscription is not None:
                self._handle_failed_subscription(object_subscription)

        object_subscription = ObjectSubscription(
            bacnet_client,
            subscription_id,
            lifetime=lifetime,
            initial_callback=callback,
            failed_subscription_callback=failed_subscription_callback,
        )
        object_subscription.callback_holder.add(release)

        self.object_subscriptions[object_id] = object_subscription

    def _handle_failed_subscription(self, object_subscription: ObjectSubscription):
        pass

    def remove_subscription(self, object_id: ObjectIdentifier):
        subscription = self.object_subscriptions.pop(object_id)

        subscription.stop_subscription()

    def get_subscription(
        self, object_id: ObjectIdentifier
    ) -> ObjectSubscription | None:
        if object_id not in self.object_subscriptions:
            return None
        return self.object_subscriptions[object_id]
