import asyncio
from collections.abc import Callable
from datetime import datetime as dt

from BAC0 import lite

from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID
from fastcs_bacnet.practical.generic.callback_stack import CallbackStack


class ObjectSubscription:
    """
    Handles and tracks subscriptions to bacnet objects
    """

    _last_subscription: dt
    _last_update: dt
    _subscription_stopped: bool = False
    callback_stack: CallbackStack[str, float]

    def __init__(
        self,
        bacnet_client: lite,
        subscription_id: SubscriptionID,
        lifetime: int = 60,
        auto_renew: bool = True,
        tracking: bool = False,
        initial_callback: Callable[[str, float], None] | None = None,
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
        self.callback_stack = CallbackStack[str, float]()

        if tracking:

            def update_last_update(
                property_identifier: str, property_value: float
            ) -> None:
                self._last_update = dt.now()

            self.callback_stack.add_to_stack(update_last_update)

        if initial_callback is not None:
            self.callback_stack.add_to_stack(initial_callback)

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

        # typing of cov's callback is TECHNICALLY [PropertyIdentifier, Any]
        # But it puts string for the first argument even though PropertyIdentifier
        # is an enum thats values are integers
        self._bacnet_client.cov(
            str(self._subscription_id.socket_address),
            self._subscription_id.object_key.to_tuple(),
            lifetime=self._lifetime,
            callback=self.callback_stack.sum_callback,
        )

        if self.auto_renew:
            event_loop = asyncio.get_running_loop()
            event_loop.call_later(self._lifetime // 2, self.subscribe)

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
