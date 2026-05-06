import asyncio
from asyncio import Lock
from collections.abc import Callable

from BAC0 import lite
from bacpypes3.pdu import Address
from bacpypes3.service.device import WhoIsFuture

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
    iam_listener_reference: asyncio.Task | None = None

    def __init__(self, bacnet_client: lite, ip_socket: IPv4SocketAddress):

        self.bacnet_client = bacnet_client
        self.ip_socket = ip_socket
        self.object_subscriptions = {}
        self.subscription_lock = SubscriptionLock()
        self.down_subscriptions = set()

    async def add_subscription(
        self,
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
            self.bacnet_client,
            subscription_id,
            lifetime=lifetime,
            initial_callback=callback,
            subscription_callback=self.check_for_restart,
            failed_subscription_callback=failed_subscription_callback,
        )
        object_subscription.callback_holder.add(release)
        object_subscription.callback_holder.add(self.check_for_restart)

        self.object_subscriptions[object_id] = object_subscription

    def _handle_failed_subscription(self, object_subscription: ObjectSubscription):
        self.down_subscriptions.add(object_subscription)

        # all subscriptions are down
        if self.down_subscriptions == self.object_subscriptions.items():
            self.iam_listener_reference = asyncio.create_task(
                self.listen_for_iam(self.restart_failed_subscriptions)
            )

    def remove_subscription(self, object_id: ObjectIdentifier):
        subscription = self.object_subscriptions.pop(object_id)

        subscription.stop_subscription()

    def get_subscription(
        self, object_id: ObjectIdentifier
    ) -> ObjectSubscription | None:
        if object_id not in self.object_subscriptions:
            return None
        return self.object_subscriptions[object_id]

    def check_for_restart(self, *args):
        if len(self.down_subscriptions) != 0:
            self.restart_failed_subscriptions()

    async def listen_for_iam(self, callback: Callable[[], None]):
        app = self.bacnet_client.this_application.app

        # this looks stupid but its exactly how they do it in BACpypes3
        # https://github.com/JoelBender/BACpypes3/blob/main/bacpypes3/service/device.py#L184
        if not hasattr(app, "_who_is_futures"):
            app._who_is_futures = []  # noqa: SLF001

        device_found = []
        while len(device_found) == 0:
            who_is_future = WhoIsFuture(
                app, Address("172.23.240.101"), None, None, 3600
            )
            # need to add the future to the list or the future will raise an exception
            app._who_is_futures.append(who_is_future)  # noqa: SLF001

            # this will wait until it hears an IAm from the given IP address
            # OR until it times out (hardcoded to an hour right now)
            # returns a list of IAms that match the IP
            # empty list means nothing was returned
            device_found = await who_is_future.future

        # maybe a comparison here to make sure it actually found the right device??
        callback()

    def restart_failed_subscriptions(self):
        pass
