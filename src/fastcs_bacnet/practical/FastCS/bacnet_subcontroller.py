import asyncio

from fastcs.attributes import AttributeIO, AttributeIORef, AttrR
from fastcs.controllers import Controller
from fastcs.util import ONCE

from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID


class AnalogOutputAttributeIORef(AttributeIORef):
    update_period: float | None = ONCE
    subscription_id: SubscriptionID | None = None


class AnalogOutputAttributeIO(AttributeIO[float, AnalogOutputAttributeIORef]):
    def __init__(self, bacnet_client: BacnetClient):
        super().__init__()

        self.bacnet_client = bacnet_client

    async def update(self, attr: AttrR[float, AnalogOutputAttributeIORef]):

        # subscription_id should never be none
        # finicky with default arguments
        if attr.io_ref.subscription_id is None:
            return

        subscription_object = self.bacnet_client.get_subscription(
            attr.io_ref.subscription_id
        )

        def actual_update(property_indentifier: str, property_value: float):
            # could add tracking data here
            asyncio.create_task(attr.update(property_value))

        subscription_object.set_callback(actual_update)


class BacnetSubController(Controller):
    def __init__(self):
        pass
