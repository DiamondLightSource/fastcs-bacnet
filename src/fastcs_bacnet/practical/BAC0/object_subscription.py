import asyncio
from collections.abc import Callable
from enum import Enum

from BAC0 import lite
from BAC0.core.functions.CoV import COVSubscription
from bacpypes3.service.cov import SubscriptionContextManager

from fastcs_bacnet.practical.BAC0.callback_holder import CovCallbackHolder
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID


class SubscriptionStatus(Enum):
    NOT_STARTED = 0
    STARTING = 1
    ACTIVE = 2
    INACTIVE = 3


class SusbcriptionObjectNotIntialisedError(Exception):
    pass


class ObjectSubscription:
    """
    Represents a single change of value subscription to a bacnet object
    """

    _subscription_object: COVSubscription | None = None
    _subscription_status: SubscriptionStatus = SubscriptionStatus.NOT_STARTED
    cov_callback_holder: CovCallbackHolder
    """
    Callback run when a subscription or resubscription fails

    Boolean parameter: True if this is the first subscription,
        False if its a resubscription
    """
    _failed_subscription_callback: Callable[[bool], None] | None
    _decorate_subscription_task: asyncio.Task | None

    def __init__(
        self,
        bacnet_client: lite,
        subscription_id: SubscriptionID,
        lifetime: int = 3600,
        failed_subscription_callback: Callable[[bool], None] | None = None,
    ):
        """
        Initialises variables and starts a subscription to a bacnet object

        bacnet_client: BAC0 bacnet device that can interact with bacnet objects
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
        self.cov_callback_holder = CovCallbackHolder()

        # If we recieve a CoV update we know the subscription is active
        def set_active(*_):
            self._subscription_status = SubscriptionStatus.ACTIVE

        self.cov_callback_holder.add(set_active)

        self._failed_subscription_callback = failed_subscription_callback

    def start_subscription_with_state(self, state: SubscriptionStatus) -> bool:
        """
        Starts the subscription to the bacnet object if it matches the input state

        Returns False if the subscription is not in the state
        """
        if self._subscription_status != state:
            return False
        self._subscription_status = SubscriptionStatus.STARTING

        self._make_new_subscription_object()
        return True

    def _make_new_subscription_object(self):
        # This is EXACTLY how address is assigned in lite.cov()
        # using a string in place of the complicated Address metaclass
        # using a BAC0.lite in place of BAC0Application
        # https://github.com/ChristianTremblay/BAC0/blob/main/BAC0/scripts/Lite.py#L516
        self._subscription_object = COVSubscription(
            address=str(self._subscription_id.socket_address),  # type: ignore
            objectID=self._subscription_id.object_id.to_tuple(),
            lifetime=self._lifetime,
            confirmed=False,
            callback=self.cov_callback_holder.run_callbacks,
            BAC0App=self._bacnet_client,  # type: ignore
        )
        self._subscription_object.task = asyncio.create_task(self._run())

        self._decorate_subscription_task = asyncio.create_task(
            self._decorate_resubscribe()
        )

        return True

    async def _run(self):
        """
        Starts the subscription

        Calls failed subscription callback if an error occurs
        """

        try:
            if self._subscription_object is not None:
                await self._subscription_object.run()
        except BaseException:
            self._on_failed_subscription(True)

    async def _decorate_resubscribe(self):
        """
        Decorates resubscription method so that failed subscription
        callback is called if an error occurs
        """

        if self._subscription_object is None:
            # TODO: change to logging
            raise SusbcriptionObjectNotIntialisedError

        # scm: subscription context manager
        scm_key = (
            self._subscription_object.address,
            self._subscription_object.process_identifier,
        )

        # poll app cov dictionary until it assigns scm
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

            # then tries to refresh subscription
            # and calls _on_failed_subscription if it doesnt work
            async def decorated_refresh_subscription(*args):

                try:
                    await refresh_subscription(*args)
                except BaseException:
                    self._on_failed_subscription(False)

            return decorated_refresh_subscription

        # replace refresh_subscription with its decorated version
        subscription_context_manager.refresh_subscription = (
            decorate_refresh_subscription(
                subscription_context_manager.refresh_subscription
            )
        )

        self._decorate_subscription_task = None

    def _on_failed_subscription(self, first_attempt: bool):
        """
        Called when subscription or resubscription fails

        first_attempt: True on subscription and False on resubscription
        """
        # TODO: Change to logging
        if first_attempt:
            print("subscription failed")
        else:
            print("resubscription failed")
        self._subscription_status = SubscriptionStatus.INACTIVE
        print("IP: ", self._subscription_id.socket_address)
        print("Object: ", self._subscription_id.object_id)
        if self._failed_subscription_callback is not None:
            self._failed_subscription_callback(first_attempt)

    def get_subscription_id(self) -> SubscriptionID:
        return self._subscription_id

    def get_status(self) -> SubscriptionStatus:
        return self._subscription_status
