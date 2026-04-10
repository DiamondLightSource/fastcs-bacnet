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
    _subscription_stopped: bool = False
    _diagnostic_callback: Callable[[str, float], None] | None = None

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
        NOTE: Having multiple subscriptions running at a time could cause issues
        """
        # TODO: Remove last subscription here so re-subscribing does not cause issues
        if self._subscription_stopped:
            return
        if self.tracking:
            self._last_subscription = dt.now()

        callback = self._decorate_callback()

        print("subscribing!!")

        # typing of cov's callback is TECHNICALLY [PropertyIdentifier, Any]
        # But it puts string for the first argument even though PropertyIdentifier
        # is an enum thats values are integers
        self._bacnet_client.cov(
            str(self._subscription_id.socket_address),
            self._subscription_id.object_key.to_tuple(),
            lifetime=self._lifetime,
            callback=callback,
        )

        if self.auto_renew:
            event_loop = asyncio.get_running_loop()
            event_loop.call_later(self._lifetime // 2, self.subscribe)

    def _decorate_callback(self) -> Callable[[str, float], None]:
        """
        Decorates the argument function manually
        Returns a new function that does 2 things:
            Sets this object's last_update field to the current time (when its called)
            Calls the callback argument function
        """

        def decorated_callback(property_identifier: str, property_value: float, **_):
            if self._subscription_stopped:
                return
            if self.tracking:
                self._last_update = dt.now()
            if self._callback is not None:
                self._callback(property_identifier, property_value)
            if self._diagnostic_callback is not None:
                self._diagnostic_callback(property_identifier, property_value)

        return decorated_callback

    def stop_subscription(self):
        """
        Stops the subscription from restarting or running a callback function
        Can't restart a subscription after its been stopped
        Create a new ObjectSubscription instead
        """
        # You cant send a "stop subscription" message to bacnet devices
        # The best we can do is wait out the last subscription
        self._subscription_stopped = True

    def is_subscription_stopped(self):
        return self._subscription_stopped

    def get_last_subscription(self) -> dt:
        return self._last_subscription

    def get_last_update(self) -> dt:
        return self._last_update

    def set_callback(self, callback: Callable[[str, float], None]):
        self._callback = callback
        # dont need to resubscribe as the subscription has a pointer to self

    def set_diagnostic_callback(
        self, diagnostic_callback: Callable[[str, float], None] | None
    ):
        """
        Called the same as a normal callback
        Having 2 variables makes setting and removing them easier
        """
        self._diagnostic_callback = diagnostic_callback
        # dont need to resubscribe as the subscription has a pointer to self
