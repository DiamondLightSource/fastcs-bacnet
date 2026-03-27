from fastcs.controllers import Controller

from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID
from fastcs_bacnet.practical.FastCS.bacnet_subcontroller import BacnetSubController


class BacnetController(Controller):
    def __init__(
        self, bacnet_client: BacnetClient, subscription_ids: list[SubscriptionID]
    ):
        location_subscription_pairs = BacnetController._sort_subscriptions(
            subscription_ids
        )

        subcontroller_index = 0
        for location in location_subscription_pairs.keys():
            # change to a named tuple?
            device_ip_address = location[0]
            device_bacnet_port = location[1]
            device_subscription_ids = location_subscription_pairs[location]

            device_controller = BacnetSubController(
                bacnet_client,
                device_ip_address,
                device_bacnet_port,
                device_subscription_ids,
            )

            self.add_sub_controller(
                f"subcontroller_{subcontroller_index}", device_controller
            )

            subcontroller_index += 1

    @staticmethod
    def _sort_subscriptions(
        subscriptions: list[SubscriptionID],
    ) -> dict[(str, int), list[SubscriptionID]]:  # type: ignore
        pass
