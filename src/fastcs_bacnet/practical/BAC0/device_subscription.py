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
    """
    Lock object specifically for Bacnet subscriptions

    Acquired with an ObjectIdentifier
    Must be released with the same ObjectIdentifier
    """

    _acquired_by = ObjectIdentifier

    async def acquire_with(self, acquired_by: ObjectIdentifier):
        """
        Acquires the lock with a specific ObjectIdentifier
        It can only be unlocked by passing this same ObjectIdentifier as an argument
        """
        valid = await super().acquire()

        if valid:
            self._acquired_by = acquired_by

        return valid

    def release_with(self, released_by: ObjectIdentifier) -> bool:
        """
        ObjectIdentifier must match the ObjectIdentifier the lock was acquired with
        Otherwise lock will not be released and False will be returned
        """

        if released_by != self._acquired_by:
            return False
        super().release()
        return True


class DeviceSubscription:
    """
    Handles all subscriptions to a specific device

    An intermediate between BacnetCleint and ObjectSubscription s
    """

    object_subscriptions: dict[ObjectIdentifier, ObjectSubscription]
    subscription_lock: SubscriptionLock
    down_subscription_ids: set[ObjectIdentifier]
    task_pool: set[asyncio.Task]
    iam_listen_task: asyncio.Task | None = None

    def __init__(self, bacnet_client: lite, ip_socket: IPv4SocketAddress):

        self.bacnet_client = bacnet_client
        self.ip_socket = ip_socket
        self.object_subscriptions = {}
        self.subscription_lock = SubscriptionLock()
        self.down_subscription_ids = set()
        self.task_pool = set()

    async def add_subscription(
        self,
        object_id: ObjectIdentifier,
        lifetime: int,
        callback: Callable[[str, float], None] | None = None,
    ):
        """
        Creates an ObjectSubscription that is handled by this object

        Subscriptions can only be created one at a time so the lock is acquired
        until the subscription is confirmed
        """

        await self.subscription_lock.acquire_with(object_id)

        def release(property_indentifier: str, property_value: float):
            if self.subscription_lock.locked():
                # Only releases if the object_key matches the one that locked it
                # This prevents other subscription notifications confirming a CoV
                self.subscription_lock.release_with(object_id)

        subscription_id = SubscriptionID(self.ip_socket, object_id)

        def failed_subscription_callback(_):
            if object_subscription is not None:
                release("", 0.0)
                self._handle_failed_subscription(subscription_id.object_key)

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
        object_subscription.callback_holder.add(self._cancel_iam)

        self.object_subscriptions[object_id] = object_subscription

    def _handle_failed_subscription(self, subscription_id: ObjectIdentifier):
        """
        The callback that is run when a subscription or resubscription fails
        """
        self.down_subscription_ids.add(subscription_id)

        # all subscriptions are down
        if self.down_subscription_ids == set(self.object_subscriptions.keys()):
            self.iam_listen_task = asyncio.create_task(
                self._listen_for_iam(self._restart_failed_subscriptions)
            )

    def remove_subscription(self, object_id: ObjectIdentifier):
        self.object_subscriptions.pop(object_id)

    def get_subscription(
        self, object_id: ObjectIdentifier
    ) -> ObjectSubscription | None:
        if object_id not in self.object_subscriptions:
            return None
        return self.object_subscriptions[object_id]

    def check_for_restart(self, *_):
        """
        Checks if any subscriptions are down, tries to restart them if so

        Arguments are not used, parameter is there to make the function
        more versatile
        """
        if len(self.down_subscription_ids) != 0:
            self._restart_failed_subscriptions()

    async def _listen_for_iam(self, callback: Callable[[], None]):
        """
        Indefinitely listens for an IAm message from the device this object represents
        """
        app = self.bacnet_client.this_application.app

        # this looks stupid but its exactly how they do it in BACpypes3
        # https://github.com/JoelBender/BACpypes3/blob/main/bacpypes3/service/device.py#L184
        if not hasattr(app, "_who_is_futures"):
            app._who_is_futures = []  # noqa: SLF001

        device_found = []
        while len(device_found) == 0:
            who_is_future = WhoIsFuture(
                app, Address(str(self.ip_socket)), None, None, 3600
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

        self.iam_listen_task = None

    def _cancel_iam(self, *_):
        if self.iam_listen_task is not None:
            self.iam_listen_task.cancel()
            self.iam_listen_task = None

    def _restart_failed_subscriptions(self):
        """
        Loops through all subscriptions in the down subscriptions set and restarts them
        """

        for down_object_subscription_id in self.down_subscription_ids:
            task = asyncio.create_task(
                self._restart_single_subscription(down_object_subscription_id)
            )
            self.task_pool.add(task)
            task.add_done_callback(self.task_pool.remove)

    async def _restart_single_subscription(self, object_identifier: ObjectIdentifier):
        """
        Restarts a single object subscription on this device
        """

        object_subscription = self.object_subscriptions[object_identifier]
        if object_subscription not in self.down_subscription_ids:
            print("raise error")

        await self.subscription_lock.acquire_with(object_identifier)

        if object_identifier not in self.down_subscription_ids:
            # subscription already restarted
            return

        # asume the restart will work
        # if it doesnt, the id will be added to this set again
        self.down_subscription_ids.discard(object_identifier)
        object_subscription = self.object_subscriptions[object_identifier]

        object_subscription.restart_subscription()

        # Trust that the object subscription still has its its release() method on
        # the callback holder??
        # There is no reason to remove it but callback_holder is public and not
        # releasing the lock would be very bad
