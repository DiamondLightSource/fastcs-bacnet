import asyncio
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
        if self.tracking:
            self.last_subscription = dt.now()

        callback = self.callback
        if self.tracking:
            callback = self._decorate_callback(self.callback)

        self.bacnet_client.cov(
            f"{self.subscription_id.address}:{self.subscription_id.port}",
            (self.subscription_id.object_type, self.subscription_id.object_id),
            lifetime=self.lifetime,
            callback=callback,
        )

        # is it bad to do this recursively rather than in a while loop??
        if self.auto_renew:
            asyncio.create_task(self._queue_subscription(self.lifetime // 2))

    async def _queue_subscription(self, queue_time):

        await asyncio.sleep(queue_time)
        self.subscribe()

    def _decorate_callback(self, callback) -> Callable[[str, float], None]:

        def decorated_callback(property_indentifier: str, property_value: float):
            self.last_update = dt.now()
            callback(property_indentifier, property_value)

        return decorated_callback
