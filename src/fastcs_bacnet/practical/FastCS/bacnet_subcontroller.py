import asyncio
from dataclasses import dataclass

from fastcs.attributes import AttributeIO, AttributeIORef, AttrR
from fastcs.controllers import Controller
from fastcs.datatypes import Float
from fastcs.util import ONCE

from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID


@dataclass
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
    def __init__(
        self,
        bacnet_client: BacnetClient,
        ip_address: str,
        port: int,
        subscription_ids: list[SubscriptionID],
    ):
        super().__init__(ios=[AnalogOutputAttributeIO(bacnet_client)])

        for subscription_id in subscription_ids:
            # TODO: Throw an error here instead
            if subscription_id.address != ip_address:
                print(f"""
                    Subcontroller address does not match subscription address
                    Subcontroller address: {ip_address}
                    Subscription address: {subscription_id.address}
                """)
            if subscription_id.port != port:
                print(f"""
                    Subcontroller port does not match subscription port
                    Subcontroller port: {port}
                    Subscription port: {subscription_id.port}
                """)

            self.add_attribute(
                f"{subscription_id.object_type}_{subscription_id.object_id}",
                AttrR(
                    Float(),
                    io_ref=AnalogOutputAttributeIORef(subscription_id=subscription_id),
                ),
            )
