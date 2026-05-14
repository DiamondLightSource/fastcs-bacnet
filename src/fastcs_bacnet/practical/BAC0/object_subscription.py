import asyncio
from collections.abc import Callable

from BAC0 import lite
from BAC0.core.functions.CoV import COVSubscription
from bacpypes3.service.cov import SubscriptionContextManager

from fastcs_bacnet.practical.BAC0.callback_holder import CallbackHolder
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID


class ObjectSubscription:
    """
    Handles subscriptions to bacnet objects
    """

    _subscription_object: COVSubscription | None = None
    _subscription_down: bool = True
    callback_holder: CallbackHolder
    _failed_subscription_callback: Callable[[bool], None] | None
    _decorate_susbcription_task: asyncio.Task

    def __init__(
        self,
        bacnet_client: lite,
        subscription_id: SubscriptionID,
        lifetime: int = 60,
        failed_subscription_callback: Callable[[bool], None] | None = None,
    ):
        """
        bacnet_client: python bacnet device that can interact with bacnet objects
        subscription_id: dataclass used to identify an object on a bacnet device
        lifetime: length of subscription (in seconds)
        failed_subscription_callback: procedure that runs when a cov request is sent out
            and fails
            The boolean parameter argument is True when it is the initial subscription
            request and False when refreshing the subscription (automatically done by
            BAC0)
        """
        self._bacnet_client = bacnet_client
        self._subscription_id = subscription_id
        self._lifetime = lifetime
        self.callback_holder = CallbackHolder()

        self._failed_subscription_callback = failed_subscription_callback

        self.restart_subscription()

    def restart_subscription(self):
        """
        Restarts the subscription to the bacnet object
        """
        if not self._subscription_down:
            print("subscrption is already up")
            return
        self._subscription_down = False

        # This is EXACTLY how address is assigned in lite.cov()
        # using a string in place of the complicated Address metaclass
        # using a BAC0.lite in place of BAC0Application
        # https://github.com/ChristianTremblay/BAC0/blob/main/BAC0/scripts/Lite.py#L516
        self._subscription_object = COVSubscription(
            address=str(self._subscription_id.socket_address),  # type: ignore
            objectID=self._subscription_id.object_key.to_tuple(),
            lifetime=self._lifetime,
            confirmed=False,
            callback=self.callback_holder.run_callbacks,
            BAC0App=self._bacnet_client,  # type: ignore
        )
        self._subscription_object.task = asyncio.create_task(self._run())

        self._decorate_susbcription_task = asyncio.create_task(
            self._decorate_resubscribe()
        )

    async def _run(self):
        """
        Calls subscription object run method with callbacks
        """

        try:
            if self._subscription_object is not None:
                await self._subscription_object.run()
        except BaseException:
            self._on_failed_subscription(True)

    async def _decorate_resubscribe(self):
        """
        Implements callbacks into resubscription method
        """

        if self._subscription_object is None:
            return

        scm_key = (
            self._subscription_object.address,
            self._subscription_object.process_identifier,
        )

        # poll app dictionary until it assigns scm
        while scm_key not in self._bacnet_client.this_application.app._cov_contexts:  # noqa: SLF001
            await asyncio.sleep(0.1)

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

    def _on_failed_subscription(self, first_attempt: bool):
        """
        Method to be called when subscription or resubscription fails

        first_attempt: True on subscription and False on resubscription
        """
        if first_attempt:
            print("subscription failed")
        else:
            print("resubscription failed")
        self._subscription_down = True
        print("IP: ", self._subscription_id.socket_address)
        print("Object: ", self._subscription_id.object_key)
        if self._failed_subscription_callback is not None:
            self._failed_subscription_callback(first_attempt)
