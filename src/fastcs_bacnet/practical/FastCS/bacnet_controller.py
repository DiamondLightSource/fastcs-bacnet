from fastcs.controllers import Controller

from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID
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
            (these will be BacnetSubcontrollers)
            Subcontroller naming convention: subcontroller_[index]
            Where [index] increments from 0 for each device in no particular order
        """
        super().__init__(ios=[])

        self.bacnet_client = bacnet_client

        location_subscription_list_pairs = BacnetController._sort_subscriptions(
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

    @staticmethod
    def _sort_subscriptions(
        subscription_ids: list[SubscriptionID],
    ) -> dict[tuple[str, int], list[SubscriptionID]]:
        """
        Sorts a list of subscription ids into lists of common locations (ip-port pairs)
        subscription_ids: A list of SubscriptionID objects to sort
            Each list of common locations is put into a dictionary where
            the key is the location
        """

        location_subscription_list_pairs: dict[
            tuple[str, int], list[SubscriptionID]
        ] = {}

        for subscription_id in subscription_ids:
            location = (subscription_id.address, subscription_id.port)

            # If the location is already in the dictionary
            # add the subscription id to the list
            if location in location_subscription_list_pairs:
                location_subscription_list_pairs[location].append(subscription_id)
            # If the location is not in the dictionary
            # create a new list for the location, it contains the subscription id
            else:
                location_subscription_list_pairs[location] = [subscription_id]

        return location_subscription_list_pairs
