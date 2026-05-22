from typing import Any

from bacpypes3.primitivedata import PropertyIdentifier
from fastcs.attributes import AttrR
from fastcs.controllers import Controller
from fastcs.datatypes import Bool, Float

from fastcs_bacnet.core.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.core.BAC0.object_subscription import ObjectSubscription
from fastcs_bacnet.core.BAC0.subscription_id import SubscriptionID
from fastcs_bacnet.core.FastCS.bacnet_attributes import (
    AnalogAttributeIO,
    AnalogAttributeIORef,
    BinaryAttributeIO,
    BinaryAttributeIORef,
)


class InvalidSubscriptionIDError(BaseException):
    pass


class InvalidObjectTypeError(BaseException):
    pass


class BacnetSubController(Controller):
    """
    A controller for a single bacnet device (IP-port pair)
    """

    def __init__(
        self,
        bacnet_client: BacnetClient,
        ip_address: str,
        subscription_ids: list[SubscriptionID],
        port: int = 47808,
    ):
        """
        Creates attributes for each subscription id given in the list

        Makes sure the ip address and the port matches each subscription
        And links CoV update callback to the FastCS Attribute

        bacnet_client: NOT a BAC0.lite object but a BacnetClient object
        ip_address: ip address of the device this controls
        subscription_ids: list of subscriptions to make attributes for
            must be objects on the device (same ip and port)
        port: the port number the device uses for bacnet communication (default 47808)
        """
        super().__init__(
            ios=[
                AnalogAttributeIO(),
                BinaryAttributeIO(),
            ]
        )

        for subscription_id in subscription_ids:
            if subscription_id.socket_address.ip_address != ip_address:
                raise InvalidSubscriptionIDError(
                    f"Subcontroller address does not match subscription address"
                    f"Subcontroller address: {ip_address}"
                    f"Subscription address: {subscription_id.socket_address.ip_address}"
                )
            if subscription_id.socket_address.port != port:
                raise InvalidSubscriptionIDError(
                    f"Subcontroller port does not match subscription port"
                    f"Subcontroller port: {port}"
                    f"Subscription port: {subscription_id.socket_address.port}"
                )
            object_subscription = bacnet_client.get_subscription(subscription_id)

            object_type_snake_case = subscription_id.object_id.object_type.replace(
                "-", "_"
            )
            attribute_name = (
                f"{object_type_snake_case}_{subscription_id.object_id.object_instance}"
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
                raise InvalidObjectTypeError(
                    "Bacnet object type was not recognised by BacnetSubcontroller"
                )


def set_subscription_callback(object_subscription: ObjectSubscription, attr: AttrR):
    """
    Links an object subscription to a FastCS Attribute

    Adds a CoV callback that updates the FastCS Attribute with its value
    """

    async def update_attribute_callback(property_identifier: str, property_value: Any):
        if property_identifier == PropertyIdentifier.presentValue:
            await attr.update(property_value)

    object_subscription.cov_callback_holder.add(update_attribute_callback)
