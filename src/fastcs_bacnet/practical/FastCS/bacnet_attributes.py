from dataclasses import dataclass

from fastcs.attributes import AttributeIO, AttributeIORef

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
        super().__init__(update_period=None)
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


class AnalogAttributeIO(AttributeIO[float, AnalogAttributeIORef]):
    """
    Docstring
    """


class BinaryAttributeIO(AttributeIO[bool, BinaryAttributeIORef]):
    """
    Docstring
    """
