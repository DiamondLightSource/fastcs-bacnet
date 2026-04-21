import asyncio
from collections.abc import Callable
from datetime import datetime as dt

from BAC0 import lite

from fastcs_bacnet.practical.BAC0.subscriptions.cov_tracker import CovTracker
from fastcs_bacnet.practical.BAC0.subscriptions.subscription_id import SubscriptionID
from fastcs_bacnet.practical.BAC0.subscriptions.subscription_status import (
    SubscriptionStatus,
    Team,
)
from fastcs_bacnet.practical.generic.callback_stack import CallbackStack


class ObjectSubscription:
    """
    Handles and tracks subscriptions to bacnet objects
    """

    _last_update: dt
    _subscription_stopped: bool = False
    callback_stack: CallbackStack[str, float]

    def __init__(
        self,
        bacnet_client: lite,
        subscription_id: SubscriptionID,
        lifetime: int = 60,
        tracking: bool = False,
        auto_start: bool = True,
        initial_callback: Callable[[str, float], None] | None = None,
    ):
        """
        bacnet_client: python bacnet device that can interact with bacnet objects
        subscription_id: dataclass used to identify an object on a bacnet device
        lifetime: length of subscription (in seconds)
        tracking: whether the object tracks last update from device object
        auto_start: If True, starts the subscription at the end of initialisation
        callback: procedure to run when subscription object recieves an
            update from the device
            Parameters are the objects property identifier and the new value
        """
        callback_stack = CallbackStack[str, float]()

        if tracking:

            def update_last_update(
                property_identifier: str, property_value: float
            ) -> None:
                self._last_update = dt.now()

            callback_stack.add_to_stack(update_last_update)

        if initial_callback is not None:
            callback_stack.add_to_stack(initial_callback)

        self.subscription_status_object = SubscriptionStatus(
            callback_stack, subscription_id, lifetime
        )

        self.red_cov_tracker = CovTracker(
            bacnet_client, Team.RED, self.subscription_status_object
        )

        self.blue_cov_tracker = CovTracker(
            bacnet_client, Team.BLUE, self.subscription_status_object
        )

        if auto_start:
            self.subscribe()

    def subscribe(self):
        """
        Starts the subscription
        """
        # TODO: reinitialise all objects so this method can also be used to
        # manually restart the subscription, whether it was stopped manually
        # OR lost the object

        self.red_cov_tracker.start_cov()

        asyncio.get_running_loop().call_later(
            self.subscription_status_object.lifetime // 2,
            self.blue_cov_tracker.start_cov,
        )

    def stop_subscription(self):
        """
        Stops the subscriptions from automatically renewing
        Also stops callbacks being called from now on
        """
        self.red_cov_tracker.stop_cov()
        self.blue_cov_tracker.stop_cov()

    def is_subscription_stopped(self):
        return self._subscription_stopped

    def get_last_update(self) -> dt:
        return self._last_update
