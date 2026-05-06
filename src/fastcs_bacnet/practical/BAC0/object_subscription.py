import asyncio
from collections.abc import Callable
from datetime import datetime as dt

from BAC0 import lite
from BAC0.core.functions.CoV import COVSubscription
from bacpypes3.service.cov import SubscriptionContextManager

from fastcs_bacnet.practical.BAC0.callback_holder import CallbackHolder
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID


class ObjectSubscription:
    """
    Handles and tracks subscriptions to bacnet objects
    """

    _last_subscription: dt
    _last_update: dt
    _subscription_object: COVSubscription | None = None
    _subscription_down: bool = True
    callback_holder: CallbackHolder
    _subscription_callback: Callable[[bool], None] | None
    _failed_subscription_callback: Callable[[bool], None] | None

    def __init__(
        self,
        bacnet_client: lite,
        subscription_id: SubscriptionID,
        lifetime: int = 60,
        tracking: bool = False,
        initial_callback: Callable[[str, float], None] | None = None,
        subscription_callback: Callable[[bool], None] | None = None,
        failed_subscription_callback: Callable[[bool], None] | None = None,
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
        initial_callback: procedure to run when subscription object recieves an
            update from the device
            Parameters are the objects property identifier and the new value
        subscription_callback: procedure that runs when a cov request is sent out
            The boolean parameter argument is True when it is the initial subscription
            request and False when refreshing the subscription (automatically done by
            BAC0)
        failed_subscription_callback: procedure that runs when a cov request is sent out
            and fails
            The boolean parameter argument is True when it is the initial subscription
            request and False when refreshing the subscription (automatically done by
            BAC0)
        """
        self._bacnet_client = bacnet_client
        self._subscription_id = subscription_id
        self._lifetime = lifetime
        self.tracking = tracking
        self.callback_holder = CallbackHolder()

        self._subscription_callback = subscription_callback
        self._failed_subscription_callback = failed_subscription_callback

        if tracking:

            def update_last_update(
                property_identifier: str, property_value: float
            ) -> None:
                self._last_update = dt.now()

            self.callback_holder.add(update_last_update)

        if initial_callback is not None:
            self.callback_holder.add(initial_callback)

        self.subscribe()

    def subscribe(self):
        """
        Restarts the subscription to the bacnet object

        Records time this method was called
        """
        if not self._subscription_down:
            print("subscrption is already up")
            return
        self._subscription_down = False

        # This is EXACTLY how address is assigned in lite.cov()
        # using a string in place of the complicated Address metaclass
        # using a BAC0.lite in place of BAC0Application
        self._subscription_object = COVSubscription(
            address=str(self._subscription_id.socket_address),  # type: ignore
            objectID=self._subscription_id.object_key.to_tuple(),
            lifetime=self._lifetime,
            confirmed=False,
            callback=self.callback_holder.run_callbacks,
            BAC0App=self._bacnet_client,  # type: ignore
        )
        self._subscription_object.task = asyncio.create_task(self._run())

        self._subscription_object.task.add_done_callback(self._decorate_resubscribe)

    async def _run(self):

        try:
            if self._subscription_object is not None:
                self._on_subscription_attempt(True)
                await self._subscription_object.run()
        except BaseException:
            self._on_failed_subscription(True)

    def _decorate_resubscribe(self, _):

        if self._subscription_object is None:
            return

        scm_key = (
            self._subscription_object.address,
            self._subscription_object.process_identifier,
        )

        # To add a callback on resubscription we need to go down to the BacPyPes3 layer
        # Specifically, we need to get the SubscriptionContextManager as this is what
        # handles the resubscription
        # Accessing the _cov_contexts private dictionary is the only way to get it
        subscription_context_manager: SubscriptionContextManager = (
            self._bacnet_client.this_application.app._cov_contexts[scm_key]  # noqa: SLF001
        )

        # manual decoration funciton
        def decorate_refresh_subscription(refresh_subscription):

            # decorated function calls _on_subscription_attempt first
            # then tries to refresh subscription
            # and calls _on_failed_subscription if it doesnt work
            async def decorated_refresh_subscription(*args):
                self._on_subscription_attempt(False)

                try:
                    await refresh_subscription(*args)
                except BaseException:
                    self._on_failed_subscription(False)

            return decorated_refresh_subscription

        # replace resfresh_subscription with its decorated version
        subscription_context_manager.refresh_subscription = (
            decorate_refresh_subscription(
                subscription_context_manager.refresh_subscription
            )
        )

    def _on_subscription_attempt(self, first_attempt: bool):
        if self.tracking:
            self._last_subscription = dt.now()
        if self._subscription_callback is not None:
            self._subscription_callback(first_attempt)

    def _on_failed_subscription(self, first_attempt: bool):
        if first_attempt:
            print("subscription failed")
        else:
            print("resubscription failed")
        self._subscription_down = True
        print("IP: ", self._subscription_id.socket_address)
        print("Object: ", self._subscription_id.object_key)
        if self._failed_subscription_callback is not None:
            self._failed_subscription_callback(first_attempt)

    def get_last_subscription(self) -> dt:
        return self._last_subscription

    def get_last_update(self) -> dt:
        return self._last_update
