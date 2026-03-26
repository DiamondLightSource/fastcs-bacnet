from collections.abc import Callable
from datetime import datetime as dt

from BAC0 import lite

from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID


class ObjectSubscription:
    last_subscription: dt
    last_update: dt

    def __init__(
        self,
        bacnet_client: lite,
        subscription_id: SubscriptionID,
        lifetime: int = 60,
        auto_renew: bool = True,
        tracking: bool = False,
        callback: Callable[[str, float], None] | None = None,
    ):
        self.bacnet_client = bacnet_client
        self.subscription_id = subscription_id
        self.lifetime = lifetime
        self.auto_renew = auto_renew
        self.tracking = tracking
        self.callback = callback

        self.subscribe()

    def subscribe(self):
        pass

    async def _queue_subscription(self, queue_time):
        pass

    def _decorated_callback(self, callback):
        pass
