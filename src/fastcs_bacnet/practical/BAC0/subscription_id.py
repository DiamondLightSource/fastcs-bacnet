from collections import defaultdict
from dataclasses import astuple, dataclass


@dataclass(frozen=True)
class IPv4SocketAddress:
    ip_address: str
    port: int

    def __str__(self):
        return self.ip_address + ":" + str(self.port)


@dataclass(frozen=True)
class ObjectIdentifier:
    object_type: str
    object_instance: int

    def to_tuple(self):
        return astuple(self)


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

    socket_address: IPv4SocketAddress
    object_key: ObjectIdentifier


def sort_subscriptions(
    subscription_ids: list[SubscriptionID],
) -> dict[IPv4SocketAddress, list[SubscriptionID]]:
    """
    Sorts a list of subscription ids into lists of IPv4SocketAddress (ip-port pairs)
    subscription_ids: A list of SubscriptionID objects to sort
        Each list of common locations is put into a dictionary where
        the key is the location
    """

    # default dict is a subclass of dict
    # if you try to index a key thats not in the dictionary
    # it runs the factory function on that key (list here, creating an empty list)
    # it then indexes the key as usual
    location_subscription_list_pairs: dict[IPv4SocketAddress, list[SubscriptionID]] = (
        defaultdict(list)
    )

    for subscription_id in subscription_ids:
        socket_address = subscription_id.socket_address

        location_subscription_list_pairs[socket_address].append(subscription_id)

    return location_subscription_list_pairs
