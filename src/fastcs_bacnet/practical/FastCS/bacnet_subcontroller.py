from typing import Any

from bacpypes3.primitivedata import PropertyIdentifier
from fastcs.attributes import AttrR
from fastcs.controllers import Controller
from fastcs.datatypes import Bool, Float

from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.object_subscription import ObjectSubscription
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID
from fastcs_bacnet.practical.FastCS.bacnet_attributes import (
    AnalogAttributeIO,
    AnalogAttributeIORef,
    BinaryAttributeIO,
    BinaryAttributeIORef,
)


class BacnetSubController(Controller):
    """
    A controller for a single device (IP-port pair)
    """

    def __init__(
        self,
        bacnet_client: BacnetClient,
        ip_address: str,
        port: int,
        subscription_ids: list[SubscriptionID],
    ):
        """
        Creates attributes for each subscription id given in the list
        Makes sure the ip address and the port matches each subscription
        bacnet_client: NOT a BAC0.lite object but a BacnetClient object
        ip_address: ip address of the device this controls
        port: the port number the device uses for bacnet communication (default 47808)
        subscription_ids: list of subscriptions to make attributes for
            must be objects on the device (same ip and port)
        """
        super().__init__(
            ios=[
                AnalogAttributeIO(bacnet_client),
                BinaryAttributeIO(bacnet_client),
            ]
        )

        for subscription_id in subscription_ids:
            # TODO: Throw an error here instead
            if subscription_id.socket_address.ip_address != ip_address:
                print(f"""
                    Subcontroller address does not match subscription address
                    Subcontroller address: {ip_address}
                    Subscription address: {subscription_id.socket_address.ip_address}
                """)
            if subscription_id.socket_address.port != port:
                print(f"""
                    Subcontroller port does not match subscription port
                    Subcontroller port: {port}
                    Subscription port: {subscription_id.socket_address.port}
                """)
            object_subscription = bacnet_client.get_subscription(subscription_id)

            if object_subscription is None:
                print("raise error??")
                return

            object_type_snake_case = subscription_id.object_key.object_type.replace(
                "-", "_"
            )
            attribute_name = (
                f"{object_type_snake_case}_{subscription_id.object_key.object_instance}"
            )

            # TODO: change this to another process once DLS-BMS is integrated
            if "analog" in attribute_name:
                attr = AttrR(
                    Float(),
                    io_ref=AnalogAttributeIORef(subscription_id=subscription_id),
                )
                self.add_attribute(attribute_name, attr)
                set_subscription_callback(object_subscription, attr)

            elif "binary" in attribute_name:
                attr = AttrR(
                    Bool(),
                    io_ref=BinaryAttributeIORef(subscription_id=subscription_id),
                )
                self.add_attribute(attribute_name, attr)
                set_subscription_callback(object_subscription, attr)

            else:
                print("error")


def set_subscription_callback(object_subscription: ObjectSubscription, attr: AttrR):

    async def update_attribute_callback(property_identifier: str, property_value: Any):
        if property_identifier == PropertyIdentifier.presentValue:
            await attr.update(property_value)

    object_subscription.callback_holder.add(update_attribute_callback)
