from collections import defaultdict
from collections.abc import Callable

from BAC0 import lite

from fastcs_bacnet.practical.BAC0.object_subscription import ObjectSubscription
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID


class BacnetClient:
    """
    Creates and stores subscription objects to bacnet objects
    Does NOT handle them
    """

    _down_subscriptions: defaultdict[str, list[ObjectSubscription]]

    def __init__(
        self,
        bacnet_client: lite,
        initial_subscriptions: list[SubscriptionID] | None = None,
        subscription_lifetime: int = 60,
        auto_renew_subscriptions: bool = False,
    ):
        """
        bacnet_client: python bacnet object used to interact with actual bacnet objects
            can use this classes disconnect method to disconnect it
            or disconnect manually outside
        initial_subscriptions: A list of SubsciptionIDs the object can use
            to make subscriptions in the constructor
            Just loops through this list and calls add_subscription
        subscription_lifetime: Time that subscriptions last (in seconds)
            this will affect the amount of traffic on the network (a message
            must be sent to renew the subscription)
        """
        self._subscription_lifetime = subscription_lifetime
        self._auto_renew_subscriptions = auto_renew_subscriptions

        self._bacnet_client = bacnet_client

        self._subscriptions: dict[SubscriptionID, ObjectSubscription] = {}
        self._down_subscriptions = defaultdict(list)

        if initial_subscriptions is not None:
            for subscription_id in initial_subscriptions:
                self.add_subscription(subscription_id)

    def add_subscription(
        self,
        subscription_id: SubscriptionID,
        callback: Callable[[str, float], None] | None = None,
    ):
        """
        Adds a new subscription object to the dictionary
        subscription_id: identifier used to find the object to subscribe to
        callback: Procedure that is called when a new value is recieved from the device
            If None no callback function will be used
        """

        # object_subscription has to be set AFTER its created
        # This is because the callback must be defined before its created
        # We cant give the ObjectSubscription in the callback
        # because we would have to type this inside the ObjectSubscription class
        object_subscription: ObjectSubscription | None = None

        def failed_subscription_callback(_):
            if object_subscription is not None:
                self._down_subscriptions[
                    subscription_id.socket_address.ip_address
                ].append(object_subscription)

        object_subscription = ObjectSubscription(
            self._bacnet_client,
            subscription_id,
            lifetime=self._subscription_lifetime,
            auto_renew=self._auto_renew_subscriptions,
            initial_callback=callback,
            failed_subscription_callback=failed_subscription_callback,
        )

        self._subscriptions[subscription_id] = object_subscription

    def remove_subscription(self, subscription_id: SubscriptionID):
        """
        Removes a subscription from the dictionary
        subscription_id: identifier used to find the object to subscribe to
        stop_subscription: if True, the subscription itself is also stopped
            Set to False if you have taken your own instance of the
            ObjectSubscription that you are still using
        """
        subscription = self._subscriptions.pop(subscription_id)

        subscription.stop_subscription()

    def get_subscription(self, subscription_id: SubscriptionID) -> ObjectSubscription:
        return self._subscriptions[subscription_id]

    def get_subscription_ids(self) -> list[SubscriptionID]:
        return list(self._subscriptions.keys())

    async def disconnect(self):
        """
        You should run this method when you are done with the python object
        The python object will essentially be useless after this
        Also stops all subscriptions
        """

        for subscription_id in self.get_subscription_ids():
            self.remove_subscription(subscription_id=subscription_id)
        await self._bacnet_client.disconnect()
