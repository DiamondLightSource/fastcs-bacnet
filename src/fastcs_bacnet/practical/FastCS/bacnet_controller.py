import asyncio

from fastcs.controllers import Controller

from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscription_id import sort_subscriptions
from fastcs_bacnet.practical.FastCS.bacnet_subcontroller import BacnetSubController


class BacnetController(Controller):
    """
    A FastCS controller for bacnet subscriptions
    """

    _start_subscriptions_task: asyncio.Task | None = None

    def __init__(self, bacnet_client: BacnetClient):
        """
        Creates a FastCS controller (and subcontrollers) from a BacnetClient object
        bacnet_client: NOT a BAC0.lite object but a BacnetClient object
            Will create subcontrollers for each device the BacnetClient is subscribed to
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
                socket_address.port,
                device_subscription_ids,
            )

            self.add_sub_controller(
                f"subcontroller_{subcontroller_index}", device_controller
            )

            subcontroller_index += 1

    def post_initialise(self):
        super().post_initialise()
        self._start_subscriptions_task = asyncio.create_task(
            self.bacnet_client.start_subscriptions()
        )

        def remove_start_subscriptions_task(*_):
            self._start_subscriptions_task = None

        self._start_subscriptions_task.add_done_callback(
            remove_start_subscriptions_task
        )
