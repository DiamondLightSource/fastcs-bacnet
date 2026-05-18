import asyncio
from dataclasses import dataclass
from typing import Any

from bacpypes3.primitivedata import PropertyIdentifier
from fastcs.attributes import AttributeIO, AttributeIORef, AttrR
from fastcs.util import ONCE

from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID

background_tasks = set()


@dataclass
class BacnetAttributeIORef(AttributeIORef):
    """
    Dataclass for referencing any subscription
    Basically just uses subscription id dataclass
    Update period must be once as this sets the attribute update callback
    """

    subscription_id: SubscriptionID
    update_period: float | None = ONCE

    def __init__(self, subscription_id: SubscriptionID):
        self.update_period = ONCE
        self.subscription_id = subscription_id


@dataclass
class AnalogAttributeIORef(BacnetAttributeIORef):
    """
    BacnetAttributeIORef specifically for analog objects
    """


@dataclass
class BinaryAttributeIORef(BacnetAttributeIORef):
    """
    BacnetAttributeIORef specifically for binary objects
    """


class BacnetAttribute:
    """
    Handler for bacnet attributes
    """

    # bacnet_client: NOT a BAC0.lite object but a BacnetClient object
    #     This is used to get ObjectSubscriptions using SubscriptionIDs
    #     You cant just pass the object susbscriptions in, you need to
    #     use the reference to get the object subscription from the bacnet_client
    bacnet_client: BacnetClient

    def set_update_attribute_callback(self, attr: AttrR[Any, BacnetAttributeIORef]):
        # subscription_id should never be none
        # finicky with default arguments
        if attr.io_ref.subscription_id is None:
            raise ValueError("Reference subscription id cannot be None")

        subscription_object = self.bacnet_client.get_subscription(
            attr.io_ref.subscription_id
        )

        if subscription_object is None:
            print("raise error")
            return

        subscription_object.callback_holder.add(
            lambda property_identifier, property_value: self.update_attribute_callback(
                attr, property_identifier, property_value
            )
        )

    def update_attribute_callback(
        self,
        attr: AttrR[Any, BacnetAttributeIORef],
        property_identifier: str,
        property_value: Any,
    ):
        if property_identifier == PropertyIdentifier.presentValue:
            # could add tracking data here
            task = asyncio.create_task(attr.update(property_value))
            background_tasks.add(task)
            # removes task from set when the task is done
            task.add_done_callback(background_tasks.discard)


class AnalogAttributeIO(AttributeIO[float, AnalogAttributeIORef], BacnetAttribute):
    """
    Handler for bacnet analog attributes
    """

    def __init__(self, bacnet_client: BacnetClient):
        super().__init__()

        self.bacnet_client = bacnet_client

    async def update(self, attr: AttrR[float, AnalogAttributeIORef]):
        """
        Perform one-time initialization that is called by FastCS during startup.

        This creates the link between the Bacnet Change-of-Value updates and the
        updating of the FastCS attribute's value.
        """

        super().set_update_attribute_callback(attr)


class BinaryAttributeIO(AttributeIO[bool, BinaryAttributeIORef], BacnetAttribute):
    """
    Handler for bacnet binary attributes
    """

    def __init__(self, bacnet_client: BacnetClient):
        super().__init__()

        self.bacnet_client = bacnet_client

    async def update(self, attr: AttrR[bool, BinaryAttributeIORef]):
        """
        Perform one-time initialization that is called by FastCS during startup.

        This creates the link between the Bacnet Change-of-Value updates and the
        updating of the FastCS attribute's value.
        """

        super().set_update_attribute_callback(attr)
