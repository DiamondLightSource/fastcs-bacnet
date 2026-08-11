from typing import Any

from bacpypes3.primitivedata import PropertyIdentifier
from fastcs.attributes import AttrR
from fastcs.controllers import Controller
from fastcs.datatypes import Bool, Float

from fastcs_bacnet.core.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.core.BAC0.object_subscription import ObjectSubscription
from fastcs_bacnet.core.BAC0.subscription_id import PVNode, SubscriptionID
from fastcs_bacnet.core.FastCS.bacnet_attributes import (
    AnalogAttributeIO,
    AnalogAttributeIORef,
    BinaryAttributeIO,
    BinaryAttributeIORef,
)


class InvalidObjectTypeError(BaseException):
    pass


class BacnetSubController(Controller):
    """
    FastCS controller for Bacnet Devices. Each Controller has attributes representing
    PVs at this controller level, and subcontrollers for deeper nested PVs.
    """

    def __init__(
        self,
        bacnet_client: BacnetClient,
        node: PVNode,
    ):
        """
        Creates attributes for each subscription id given in the list

        Makes sure the ip address and the port matches each subscription
        And links CoV update callback to the FastCS Attribute

        bacnet_client: NOT a BAC0.lite object but a BacnetClient object
        ip_address: ip address of the device this controls
        subscription_ids: list of subscriptions to make attributes for
            must be objects on the device (same ip and port)
        pv_names_dict: A mapping from SubscriptionID s (representing objects on devices)
            to the name its respective EPICS PV should be given
        port: the port number the device uses for bacnet communication (default 47808)
        """
        super().__init__(
            ios=[
                AnalogAttributeIO(),
                BinaryAttributeIO(),
            ]
        )

        self.add_attributes(bacnet_client, node.suffix)

        # Create subcontrollers
        for device_name, child_node in node.children.items():
            controller = BacnetSubController(bacnet_client, child_node)
            self.add_sub_controller(device_name, controller)

    def add_attributes(
        self, bacnet_client: BacnetClient, pvs: dict[str, SubscriptionID]
    ) -> None:
        """Create the PVs associated with this subcontroller"""
        # Create attribute for each suffix
        for pv, subscription_id in pvs.items():
            object_subscription = bacnet_client.get_subscription(subscription_id)

            attr = self._create_attribute(subscription_id)

            self.add_attribute(pv, attr)
            set_subscription_callback(object_subscription, attr)

    def _create_attribute(
        self, subscription_id: SubscriptionID
    ) -> AttrR[float, AnalogAttributeIORef] | AttrR[bool, BinaryAttributeIORef]:
        if "analog" in subscription_id.object_id.object_type:
            attr = AttrR(
                Float(),
                io_ref=AnalogAttributeIORef(subscription_id=subscription_id),
            )

        elif "binary" in subscription_id.object_id.object_type:
            attr = AttrR(
                Bool(),
                io_ref=BinaryAttributeIORef(subscription_id=subscription_id),
            )

        else:
            raise InvalidObjectTypeError(
                f"Bacnet object type was not recognised by BacnetSubcontroller "
                f"object type: {subscription_id.object_id.object_type}"
            )
        return attr


def set_subscription_callback(object_subscription: ObjectSubscription, attr: AttrR):
    """
    Links an object subscription to a FastCS Attribute

    Adds a CoV callback that updates the FastCS Attribute with its value
    """

    async def update_attribute_callback(property_identifier: str, property_value: Any):
        if property_identifier == PropertyIdentifier.presentValue:
            await attr.update(property_value)

    object_subscription.cov_callback_holder.add(update_attribute_callback)
