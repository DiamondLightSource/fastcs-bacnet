from collections.abc import Callable

from BAC0 import lite, start

from fastcs_bacnet.practical.BAC0.object_subscription import ObjectSubscription
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID


class BacnetClient:
    def __init__(
        self,
        bacnet_client: lite | None = None,
        initial_subscriptions: list[SubscriptionID] | None = None,
        subscription_lifetime: int = 60,
        default_generic_callback: Callable[[SubscriptionID, str, float], None]
        | None = None,
    ):
        self.subscription_lifetime = subscription_lifetime
        self.defualt_generic_callback = default_generic_callback

        if bacnet_client is not None:
            self.bacnet_client = bacnet_client
            self.borrowed_deivce = False
        else:
            # these are not good forced parameters
            # maybe its just better to force users to give a bacnet_client??
            self.bacnet_client = start("127.0.0.1", 47808, deviceId=1)
            self.borrowed_deivce = True

        self.subscriptions: dict[SubscriptionID, ObjectSubscription] = {}

        if initial_subscriptions is not None:
            for subscription_id in initial_subscriptions:
                self.add_subscription(subscription_id)

    def add_subscription(
        self,
        subscription_id: SubscriptionID,
        callback: Callable[[str, float]] | None = None,
    ):
        pass

    def remove_subscription(self, subscription_id: SubscriptionID):
        pass

    def get_subscription(self, subscription_id: SubscriptionID) -> ObjectSubscription:  # type: ignore
        pass

    def disconnect(self):
        pass
