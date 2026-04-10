from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class SubscriptionID:
    """
    dataclass for identifying a specific bacnet object to subscribe to
    address: ip address of the device that owns the object
        in string format (e.g. "127.0.0.1")
    port: port device is using for bacnet communication (e.g. 47808)
    object_type: type of object belonging to the bacnet device (e.g. "analog-output")
    object_id: instance number for this object on the device (e.g. 0)
    """

    address: str
    port: int
    object_type: str
    object_id: int

    def socket_address(self) -> str:
        return f"{self.address}:{self.port}"

    def object_key(self) -> tuple[str, int]:
        return (self.object_type, self.object_id)


def sort_subscriptions(
    subscription_ids: list[SubscriptionID],
) -> dict[tuple[str, int], list[SubscriptionID]]:
    """
    Sorts a list of subscription ids into lists of common locations (ip-port pairs)
    subscription_ids: A list of SubscriptionID objects to sort
        Each list of common locations is put into a dictionary where
        the key is the location
    """

    # default dict is a subclass of dict
    # if you try to index a key thats not in the dictionary
    # it runs the factory function on that key (list here, creating an empty list)
    # it then indexes the key as usual
    location_subscription_list_pairs: dict[tuple[str, int], list[SubscriptionID]] = (
        defaultdict(list)
    )

    for subscription_id in subscription_ids:
        location = (subscription_id.address, subscription_id.port)

        location_subscription_list_pairs[location].append(subscription_id)

    return location_subscription_list_pairs
