from collections.abc import Callable

from BAC0 import lite, start

from fastcs_bacnet.practical.BAC0.object_subscription import ObjectSubscription
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID


class BacnetClient:
    """
    Creates and stores subscription objects to bacnet objects
    Does NOT handle them
    """

    def __init__(
        self,
        bacnet_client: lite | None = None,
        initial_subscriptions: list[SubscriptionID] | None = None,
        subscription_lifetime: int = 60,
        default_generic_callback: Callable[[SubscriptionID, str, float], None]
        | None = None,
    ):
        """
        bacnet_client: python bacnet object used to interact with actual bacnet objects
            if set to None one is created inside the object
            if one is created remember to disconnect it using the disconnect method
        initial_subscriptions: A list of SubsciptionIDs the object can use
            to make subscriptions in the constructor
            Just loops through this list and calls add_subscription
        subscription_lifetime: Time that subscriptions last (in seconds)
            subscriptions are auto renewed so this doesnt matter too much
        default_generic_callback: Callbacks can be added to subscriptions
            (procedures that run when a new value is recieved from the device)
            This is a generic callback that can apply to any subscription and takes
            its SubscriptionID as a parameter
            This will be used as a defualt for added subscriptions
            If None nothing happens when a new value is recieved
        """
        self._subscription_lifetime = subscription_lifetime
        self._default_generic_callback = default_generic_callback

        if bacnet_client is not None:
            self._bacnet_client = bacnet_client
            self._borrowed_device = False
        else:
            # these are not good forced parameters
            # maybe its just better to force users to give a bacnet_client??
            self._bacnet_client = start("127.0.0.1", 47808, deviceId=1)
            self._borrowed_device = True

        self._subscriptions: dict[SubscriptionID, ObjectSubscription] = {}

        if initial_subscriptions is not None:
            for subscription_id in initial_subscriptions:
                self.add_subscription(subscription_id)

    def add_subscription(
        self,
        subscription_id: SubscriptionID,
        callback: Callable[[str, float]] | None = None,
    ):
        """
        Adds a new subscription object to the dictionary
        subscription_id: identifier used to find the object to subscribe to
        callback: Procedure that is called when a new value is recieved from the device
            If None the default_generic_callback will be used
        """
        # cant do the check for default_generic_callback being none here
        # because it could change
        if callback is None:

            def default_callback(property_indentifier: str, property_value: float):
                if self._default_generic_callback is not None:
                    self._default_generic_callback(
                        subscription_id, property_indentifier, property_value
                    )

            callback = default_callback

        self._subscriptions[subscription_id] = ObjectSubscription(
            self._bacnet_client,
            subscription_id,
            lifetime=self._subscription_lifetime,
            callback=callback,
        )

    def remove_subscription(
        self, subscription_id: SubscriptionID, stop_subscription=True
    ):
        """
        Removes a subscription from the dictionary
        subscription_id: identifier used to find the object to subscribe to
        stop_subscription: if True, the subsciption itself is also stopped
            Set to False if you have taken your own instance of the
            ObjectSubscription that you are still using
        """
        subscription = self.get_subscription(subscription_id)
        self._subscriptions.pop(subscription_id)

        if stop_subscription:
            subscription.stop_subscription()

    def get_subscription(self, subscription_id: SubscriptionID) -> ObjectSubscription:
        return self._subscriptions[subscription_id]

    def get_subscription_ids(self) -> list[SubscriptionID]:
        return list(self._subscriptions.keys())

    def is_device_borrowed(self) -> bool:
        return self._borrowed_device

    async def disconnect(self):
        """
        If a bacnet client was made on the initialisation of this class
        (bacnet_client = None on object creation)
        You should run this method when you are done with the python object
        The python object will essentially be useless after this
        Also stops all subscriptions
        """

        if self._borrowed_device:
            return

        for subscription_id in self.get_subscription_ids():
            self.remove_subscription(subscription_id=subscription_id)
        await self._bacnet_client.disconnect()
