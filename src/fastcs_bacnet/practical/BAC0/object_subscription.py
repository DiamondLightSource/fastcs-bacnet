import asyncio
from collections.abc import Callable
from datetime import datetime as dt

from BAC0 import lite

from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID


class ObjectSubscription:
    """
    Handles and tracks subscriptions to bacnet objects
    """

    _last_subscription: dt
    _last_update: dt

    def __init__(
        self,
        bacnet_client: lite,
        subscription_id: SubscriptionID,
        lifetime: int = 60,
        auto_renew: bool = True,
        tracking: bool = False,
        callback: Callable[[str, float], None] | None = None,
    ):
        """
        bacnet_client: python bacnet device that can interact with bacnet objects
        subscription_id: dataclass used to identify an object on a bacnet device
        lifetime: length of subscription (in seconds)
        auto_renew: whether the object automatically restarts its subscription
            This will happen half way through the subscriptions lifetime
            You can still use the subscribe method to restart the subscription manually
        tracking: whether the object tracks:
            last subscription time
            last update from device subscription
        callback: procedure to run when subscription object recieves an
            update from the device
            Parameters are the objects property identifier and the new value
        """
        self._bacnet_client = bacnet_client
        self._subscription_id = subscription_id
        self._lifetime = lifetime
        self.auto_renew = auto_renew
        self.tracking = tracking
        self._callback = callback

        self.subscribe()

    def subscribe(self):
        """
        Restarts the subscription to the bacnet object
        Records time this method was called
        """
        if self.tracking:
            self._last_subscription = dt.now()

        callback = self._callback
        if self.tracking and self._callback is not None:
            callback = self._decorate_callback(self._callback)

        self._bacnet_client.cov(
            f"{self._subscription_id.address}:{self._subscription_id.port}",
            (self._subscription_id.object_type, self._subscription_id.object_id),
            lifetime=self._lifetime,
            callback=callback,
        )

        # is it bad to do this recursively rather than in a while loop??
        if self.auto_renew:
            asyncio.create_task(self._queue_subscription(self._lifetime // 2))

    async def _queue_subscription(self, queue_time: int):
        """
        Calls subscription in [queue time] seconds
        """

        await asyncio.sleep(queue_time)
        self.subscribe()

    def _decorate_callback(
        self, callback: Callable[[str, float], None]
    ) -> Callable[[str, float], None]:
        """
        Decorates the argument function manually
        Returns a new function that does 2 things:
            Sets this object's last_update field to the current time (when its called)
            Calls the callback argument function
        """

        def decorated_callback(property_indentifier: str, property_value: float):
            self._last_update = dt.now()
            callback(property_indentifier, property_value)

        return decorated_callback

    def get_last_subscription(self) -> dt:
        return self._last_subscription

    def get_last_update(self) -> dt:
        return self._last_update

    def set_callback(self, callback: Callable[[str, float], None]):
        self._callback = callback
        self.subscribe()
