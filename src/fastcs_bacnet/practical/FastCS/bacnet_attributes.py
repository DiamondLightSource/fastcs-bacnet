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

    def __init__(self, subscription_id: SubscriptionID):
        super().__init__(update_period=ONCE)
        self.subscription_id = subscription_id


@dataclass(init=False)
class AnalogAttributeIORef(BacnetAttributeIORef):
    """
    BacnetAttributeIORef specifically for analog objects
    """


@dataclass(init=False)
class BinaryAttributeIORef(BacnetAttributeIORef):
    """
    BacnetAttributeIORef specifically for binary objects
    """


class BacnetAttributeIO[T: float | bool, U: BacnetAttributeIORef](AttributeIO[T, U]):
    """
    Handler for bacnet attributes
    """

    # bacnet_client: NOT a BAC0.lite object but a BacnetClient object
    #     This is used to get ObjectSubscriptions using SubscriptionIDs
    #     You cant just pass the object susbscriptions in, you need to
    #     use the reference to get the object subscription from the bacnet_client
    bacnet_client: BacnetClient

    def __init__(self, bacnet_client: BacnetClient, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bacnet_client = bacnet_client

    async def update(self, attr: AttrR[Any, BacnetAttributeIORef]):
        """
        Perform one-time initialization that is called by FastCS during startup.

        This creates the link between the Bacnet Change-of-Value updates and the
        updating of the FastCS attribute's value.
        """

        print("update")


class AnalogAttributeIO(BacnetAttributeIO[float, AnalogAttributeIORef]):
    """
    Handler for bacnet analog attributes
    """


class BinaryAttributeIO(BacnetAttributeIO[bool, BinaryAttributeIORef]):
    """
    Handler for bacnet binary attributes
    """
