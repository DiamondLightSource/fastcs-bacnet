import asyncio

from fastcs.controllers import Controller

from fastcs_bacnet.core.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.core.BAC0.subscription_id import SubscriptionID, sort_subscriptions
from fastcs_bacnet.core.FastCS.bacnet_subcontroller import BacnetSubController


class BacnetController(Controller):
    """
    A FastCS controller for bacnet subscriptions
    """

    _start_subscriptions_task: asyncio.Task | None = None

    def __init__(
        self,
        bacnet_client: BacnetClient,
        pv_names_dict: dict[SubscriptionID, str],
    ):
        """
        Creates a FastCS controller (and subcontrollers) from a BacnetClient object

        bacnet_client: NOT a BAC0.lite object but a BacnetClient object
            Will create subcontrollers for each device
            and attributes for each subscription
        pv_names_dict: A mapping from SubscriptionID s (representing objects on devices)
            to the name of the name its repsective EPICS PV should be given
        """
        super().__init__(ios=[])

        self.bacnet_client = bacnet_client

        socket_address_subscription_list_pairs = sort_subscriptions(
            self.bacnet_client.get_subscription_ids()
        )

        subcontroller_index = 0
        for (
            socket_address,
            device_subscription_ids,
        ) in socket_address_subscription_list_pairs.items():
            device_controller = BacnetSubController(
                self.bacnet_client,
                socket_address.ip_address,
                device_subscription_ids,
                pv_names_dict,
                port=socket_address.port,
            )

            self.add_sub_controller(
                f"subcontroller_{subcontroller_index}", device_controller
            )

            subcontroller_index += 1

    def post_initialise(self):
        """
        Sends out CoV subscriptions to all Bacnet objects
        """
        super().post_initialise()
        self._start_subscriptions_task = asyncio.create_task(
            self.bacnet_client.start_subscriptions()
        )

        def remove_start_subscriptions_task(*_):
            self._start_subscriptions_task = None

        self._start_subscriptions_task.add_done_callback(
            remove_start_subscriptions_task
        )
