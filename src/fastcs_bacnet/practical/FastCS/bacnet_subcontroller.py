import asyncio
from dataclasses import dataclass

from bacpypes3.primitivedata import PropertyIdentifier
from fastcs.attributes import AttributeIO, AttributeIORef, AttrR
from fastcs.controllers import Controller
from fastcs.datatypes import Float
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

    update_period: float | None = ONCE
    subscription_id: SubscriptionID | None = None


@dataclass
class AnalogAttributeIORef(BacnetAttributeIORef):
    """
    BacnetAttributeIORef specifically for analog objects
    """


@dataclass
class BinaryAttributeIORef(BacnetAttributeIORef):
    """
    BacnetAttributeIORef specifically for analog objects
    """


class BacnetAttributeIO(AttributeIO[float, BacnetAttributeIORef]):
    """
    Handler for bacnet attributes
    """

    def __init__(self, bacnet_client: BacnetClient):
        """
        bacnet_client: NOT a BAC0.lite object but a BacnetClient object
            This is used to get ObjectSubscriptions using SubscriptionIDs
            You cant just pass the object susbscriptions in, you need to
            use the reference to get the object subscription from the bacnet_client
        """
        super().__init__()

        self.bacnet_client = bacnet_client

    async def update(self, attr: AttrR[float, BacnetAttributeIORef]):
        """
        Misnomer, does not actually update the variable in this case
        It doesnt start the subscription either
        It changes the callback on the subscription to update the attribute
        (this is the actual_update procedure)
        This is why it only needs to be run once
        """

        # subscription_id should never be none
        # finicky with default arguments
        if attr.io_ref.subscription_id is None:
            raise ValueError

        subscription_object = self.bacnet_client.get_subscription(
            attr.io_ref.subscription_id
        )

        if subscription_object is None:
            print("raise error")
            return

        def actual_update(property_indentifier: str, property_value: float):
            if property_indentifier == PropertyIdentifier.presentValue:
                # could add tracking data here
                task = asyncio.create_task(attr.update(property_value))
                background_tasks.add(task)
                # removes task from set when the task is done
                task.add_done_callback(background_tasks.discard)

        subscription_object.callback_holder.add(actual_update)


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
        super().__init__(ios=[BacnetAttributeIO(bacnet_client)])

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

            object_type_snake_case = subscription_id.object_key.object_type.replace(
                "-", "_"
            )
            attribute_name = (
                f"{object_type_snake_case}_{subscription_id.object_key.object_instance}"
            )
            self.add_attribute(
                attribute_name,
                AttrR(
                    Float(),
                    io_ref=BacnetAttributeIORef(subscription_id=subscription_id),
                ),
            )
