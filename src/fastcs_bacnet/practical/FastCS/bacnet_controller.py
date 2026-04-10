from fastcs.controllers import Controller

from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscription_id import sort_subscriptions
from fastcs_bacnet.practical.FastCS.bacnet_subcontroller import BacnetSubController


class BacnetController(Controller):
    """
    A FastCS controller for bacnet subscriptions
    """

    def __init__(self, bacnet_client: BacnetClient):
        """
        Creates a FastCS controller (and subcontrollers) from a BacnetClient object
        bacnet_client: NOT a BAC0.lite object but a BacnetClient object
            Will create subcontrollers for each device the BacnetClient is subscribed to
        """
        super().__init__(ios=[])

        self.bacnet_client = bacnet_client

        location_subscription_list_pairs = sort_subscriptions(
            self.bacnet_client.get_subscription_ids()
        )

        subcontroller_index = 0
        for location in location_subscription_list_pairs.keys():
            # change to a named tuple?
            device_ip_address = location[0]
            device_bacnet_port = location[1]
            device_subscription_ids = location_subscription_list_pairs[location]

            device_controller = BacnetSubController(
                self.bacnet_client,
                device_ip_address,
                device_bacnet_port,
                device_subscription_ids,
            )

            self.add_sub_controller(
                f"subcontroller_{subcontroller_index}", device_controller
            )

            subcontroller_index += 1
