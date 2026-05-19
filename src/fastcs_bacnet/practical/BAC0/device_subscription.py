import asyncio
from asyncio import Lock

from BAC0 import lite
from bacpypes3.pdu import Address
from bacpypes3.service.device import WhoIsFuture

from fastcs_bacnet.practical.BAC0.callback_holder import CovCallback
from fastcs_bacnet.practical.BAC0.object_subscription import (
    ObjectSubscription,
    SubscriptionStatus,
)
from fastcs_bacnet.practical.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)


class SubscriptionLock:
    """
    Lock object specifically for Bacnet subscriptions

    Acquired with an ObjectIdentifier
    Must be released with the same ObjectIdentifier
    """

    _lock: Lock
    _acquired_by: ObjectIdentifier

    def __init__(self):
        self._lock = Lock()

    async def acquire_with(self, acquired_by: ObjectIdentifier):
        """
        Acquires the lock with a specific ObjectIdentifier
        It can only be unlocked by passing this same ObjectIdentifier as an argument
        """
        valid = await self._lock.acquire()

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
        self._lock.release()
        return True

    def locked(self) -> bool:
        return self._lock.locked()


class DeviceSubscription:
    """
    Handles all subscriptions to a specific device

    An intermediate between BacnetClient and ObjectSubscription s
    """

    _object_subscriptions: dict[ObjectIdentifier, ObjectSubscription]
    _subscription_lock: SubscriptionLock
    _task_pool: set[asyncio.Task]

    def __init__(self, bacnet_client: lite, socket_address: IPv4SocketAddress):

        self.bacnet_client = bacnet_client
        self.socket_address = socket_address
        self._object_subscriptions = {}
        self._subscription_lock = SubscriptionLock()
        self._task_pool = set()

        asyncio.create_task(self._listen_for_iam())

    async def add_subscription(
        self,
        object_id: ObjectIdentifier,
        lifetime: int,
        callback: CovCallback | None = None,
    ):
        """
        Creates an ObjectSubscription that is handled by this object

        Subscriptions can only be created one at a time so the lock is acquired
        until the subscription is confirmed
        """

        await self._subscription_lock.acquire_with(object_id)

        def release(*_):
            if self._subscription_lock.locked():
                # Only releases if the object_id matches the one that locked it
                # This prevents other subscription notifications confirming a CoV
                self._subscription_lock.release_with(object_id)

        subscription_id = SubscriptionID(self.socket_address, object_id)

        def on_subscription_fail(_):
            if object_subscription is not None:
                release()

        object_subscription = ObjectSubscription(
            self.bacnet_client,
            subscription_id,
            lifetime=lifetime,
            failed_subscription_callback=on_subscription_fail,
        )

        if callback is not None:
            object_subscription.callback_holder.add(callback)
        object_subscription.callback_holder.add(release)
        object_subscription.callback_holder.add(self._restart_inactive_subscriptions)

        self._object_subscriptions[object_id] = object_subscription

        self._subscription_lock.release_with(subscription_id.object_key)

    def remove_subscription(self, object_id: ObjectIdentifier):
        self._object_subscriptions.pop(object_id)

    def get_subscription(
        self, object_id: ObjectIdentifier
    ) -> ObjectSubscription | None:
        if object_id not in self._object_subscriptions:
            return None
        return self._object_subscriptions[object_id]

    def get_subscription_ids(self) -> set[SubscriptionID]:
        return {
            subscription.get_subscription_id()
            for subscription in self._object_subscriptions.values()
        }

    async def _listen_for_iam(self):
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
                app, Address(str(self.socket_address)), None, None, 3600
            )
            # need to add the future to the list or the future will raise an exception
            app._who_is_futures.append(who_is_future)  # noqa: SLF001

            # this will wait until it hears an IAm from the given IP address
            # OR until it times out (hardcoded to an hour right now)
            # returns a list of IAms that match the IP
            # empty list means nothing was returned
            device_found = await who_is_future.future

        await self._restart_inactive_subscriptions()

        # restarts the listening task
        task = asyncio.create_task(self._listen_for_iam())
        self._task_pool.add(task)
        task.add_done_callback(self._task_pool.discard)

    async def _restart_inactive_subscriptions(self, *_):
        """
        Loops through all subscriptions and restart the inactive ones
        """

        for (
            object_identifier,
            object_subscription,
        ) in self._object_subscriptions.items():
            if object_subscription.get_status == SubscriptionStatus.INACTIVE:
                await self._subscription_lock.acquire_with(object_identifier)

                # If the restart doesnt work release the lock
                if not object_subscription.restart_subscription():
                    self._subscription_lock.release_with(object_identifier)

    async def start_subscriptions(self, *_):
        """
        Loops through all subscriptions and starts the not started ones
        """

        for (
            object_identifier,
            object_subscription,
        ) in self._object_subscriptions.items():
            if object_subscription.get_status == SubscriptionStatus.NOT_STARTED:
                await self._subscription_lock.acquire_with(object_identifier)

                # If the restart doesnt work release the lock
                if not object_subscription.start_subscription():
                    self._subscription_lock.release_with(object_identifier)
