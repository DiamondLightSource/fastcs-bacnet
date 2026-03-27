from fastcs.controllers import Controller

from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID
from fastcs_bacnet.practical.FastCS.bacnet_subcontroller import BacnetSubController


class BacnetController(Controller):
    def __init__(self, bacnet_client: BacnetClient):
        location_subscription_pairs = BacnetController._sort_subscriptions(
            bacnet_client.get_subscription_ids()
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
        subscription_ids: list[SubscriptionID],
    ) -> dict[tuple[str, int], list[SubscriptionID]]:

        location_subscription_pairs: dict[tuple[str, int], list[SubscriptionID]] = {}

        for subscription_id in subscription_ids:
            location = (subscription_id.address, subscription_id.port)
            if location in location_subscription_pairs:
                location_subscription_pairs[location].append(subscription_id)
            else:
                location_subscription_pairs[location] = [subscription_id]

        return location_subscription_pairs
