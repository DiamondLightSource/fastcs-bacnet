from dataclasses import dataclass

from fastcs.attributes import AttributeIO, AttributeIORef

from fastcs_bacnet.core.BAC0.subscription_id import SubscriptionID

background_tasks = set()


@dataclass
class BacnetAttributeIORef(AttributeIORef):
    """
    FastCS attribute reference for any bacnet object

    subscription_id: id of the object this is referencing
    """

    subscription_id: SubscriptionID

    def __init__(self, subscription_id: SubscriptionID):
        super().__init__(update_period=None)
        self.subscription_id = subscription_id


@dataclass(init=False)
class AnalogAttributeIORef(BacnetAttributeIORef):
    """
    FastCS attribute reference for analog bacnet object
    """


@dataclass(init=False)
class BinaryAttributeIORef(BacnetAttributeIORef):
    """
    FastCS attribute reference for binary bacnet object
    """


class AnalogAttributeIO(AttributeIO[float, AnalogAttributeIORef]):
    """
    FastCS attribute for analog Bacnet objects
    """


class BinaryAttributeIO(AttributeIO[bool, BinaryAttributeIORef]):
    """
    FastCS attribute for binary Bacnet objects
    """
