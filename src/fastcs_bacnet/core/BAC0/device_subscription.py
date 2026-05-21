import asyncio
from asyncio import Lock

from BAC0 import lite
from bacpypes3.pdu import Address
from bacpypes3.service.device import WhoIsFuture
from fastcs.logging import logger

from fastcs_bacnet.core.BAC0.callback_holder import CovCallback
from fastcs_bacnet.core.BAC0.object_subscription import (
    ObjectSubscription,
    SubscriptionStatus,
)
from fastcs_bacnet.core.BAC0.subscription_id import (
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
    _socket_address: IPv4SocketAddress

    def __init__(self, socket_address: IPv4SocketAddress):
        self._lock = Lock()
        self._socket_address = socket_address

    async def acquire_with(self, acquired_by: ObjectIdentifier):
        """
        Acquires the lock with a specific ObjectIdentifier

        Object can only be unlocked by passing this same ObjectIdentifier as an argument
        """
        valid = await self._lock.acquire()

        if valid:
            self._acquired_by = acquired_by
            logger.debug(
                "Lock "
                + str(self._socket_address)
                + " acquired by "
                + str(acquired_by)
                + ""
            )
        else:
            logger.debug(
                "Lock "
                + str(self._socket_address)
                + " failed to be acquired by "
                + str(acquired_by)
                + ""
            )

        return valid

    def release_with(self, released_by: ObjectIdentifier) -> bool:
        """
        Attempts to release the lock with an ObjectIdentifier

        released_by: ObjectIdentifier to release the lock with.
            Will only unlock if the ObjectIdentifier matches the one
            the lock was acquired with

        return: True if unlocked successfully, False otherwise
        """

        if released_by != self._acquired_by:
            logger.debug(
                "Lock "
                + str(self._socket_address)
                + " failed to be released by "
                + str(released_by)
                + ""
            )
            return False
        logger.debug(
            "Lock "
            + str(self._socket_address)
            + " released by "
            + str(released_by)
            + ""
        )
        self._lock.release()
        return True

    def locked(self) -> bool:
        return self._lock.locked()


class DeviceSubscription:
    """
    Stores all subscriptions to a specific device

    For recording and handling down subscriptions
    An intermediate between BacnetClient and ObjectSubscription s
    """

    _object_subscriptions: dict[ObjectIdentifier, ObjectSubscription]
    _subscription_lock: SubscriptionLock
    _task_pool: set[asyncio.Task]

    def __init__(self, bacnet_client: lite, socket_address: IPv4SocketAddress):
        """
        Initialises variables and starts Iam listening process

        bacnet_client: BAC0 device object for listening to Bacnet network
        socket_address: Address of the device this object represents
        """

        self._bacnet_client = bacnet_client
        self._socket_address = socket_address
        self._object_subscriptions = {}
        self._subscription_lock = SubscriptionLock(socket_address)
        self._task_pool = set()

        asyncio.create_task(self._listen_for_iam())

    def add_subscription(
        self,
        object_id: ObjectIdentifier,
        lifetime: int,
        callback: CovCallback | None = None,
    ):
        """
        Creates a subscription to a bacnet device but does not start it
        """

        if object_id in self._object_subscriptions:
            logger.error(
                f"""Subscription for object
                 {str(object_id)}
                already exists on device
                {str(object_id)} """
            )
            return

        def release(*_):
            if self._subscription_lock.locked():
                # Only releases if the object_id matches the one that locked it
                # This prevents other subscription notifications confirming a CoV
                self._subscription_lock.release_with(object_id)

        subscription_id = SubscriptionID(self._socket_address, object_id)

        def on_subscription_fail(_):
            if object_subscription is not None:
                release()

        object_subscription = ObjectSubscription(
            self._bacnet_client,
            subscription_id,
            lifetime=lifetime,
            failed_subscription_callback=on_subscription_fail,
        )

        if callback is not None:
            object_subscription.cov_callback_holder.add(callback)
        # If the CoV request comes back with a valid response release the lock
        # this will happen every time a CoV update is received but it wont matter
        object_subscription.cov_callback_holder.add(release)
        object_subscription.cov_callback_holder.add(
            lambda *_: self._start_subscriptions_from_state(SubscriptionStatus.INACTIVE)
        )

        self._object_subscriptions[object_id] = object_subscription

    def remove_subscription(self, object_id: ObjectIdentifier):
        self._object_subscriptions.pop(object_id)

    def get_subscription(self, object_id: ObjectIdentifier) -> ObjectSubscription:
        return self._object_subscriptions[object_id]

    def get_subscription_ids(self) -> set[SubscriptionID]:
        return {
            subscription.get_subscription_id()
            for subscription in self._object_subscriptions.values()
        }

    async def _listen_for_iam(self):
        """
        Indefinitely listens for an IAm message from the device this object represents

        When one is recieved, all down subscriptions are restarted
        """
        app = self._bacnet_client.this_application.app

        # This looks stupid but its exactly how they do it in BACpypes3
        # https://github.com/JoelBender/BACpypes3/blob/main/bacpypes3/service/device.py#L184
        if not hasattr(app, "_who_is_futures"):
            app._who_is_futures = []  # noqa: SLF001

        device_found = []
        while len(device_found) == 0:
            who_is_future = WhoIsFuture(
                app, Address(str(self._socket_address)), None, None, 3600
            )
            # In future handling code app needs to remove future from the list
            # An exception will be raised if we dont add it
            app._who_is_futures.append(who_is_future)  # noqa: SLF001

            # This will wait until it hears an IAm from the given IP address
            # OR until it times out (hardcoded to an hour right now)
            # returns a list of IAms that match the IP
            # empty list means nothing was returned
            device_found = await who_is_future.future

        logger.debug(f"Recieved Iam from device {self._socket_address}")

        await self._start_subscriptions_from_state(SubscriptionStatus.INACTIVE)

        # restarts the listening task
        task = asyncio.create_task(self._listen_for_iam())
        self._task_pool.add(task)
        task.add_done_callback(self._task_pool.discard)

    async def start_subscriptions(self):
        await self._start_subscriptions_from_state(SubscriptionStatus.NOT_STARTED)

    async def _start_subscriptions_from_state(self, state: SubscriptionStatus):
        """
        Loops through all subscriptions and starts the ones in a specific state
        """

        for (
            object_identifier,
            object_subscription,
        ) in self._object_subscriptions.items():
            if object_subscription.get_status() == state:
                # Lock will be released when the initial subscription CoV is recieved
                await self._subscription_lock.acquire_with(object_identifier)

                # Alternatively, if the restart doesnt work release the lock
                if not object_subscription.start_subscription_with_state(state):
                    self._subscription_lock.release_with(object_identifier)
