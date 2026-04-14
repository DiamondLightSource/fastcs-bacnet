from collections import defaultdict
from dataclasses import astuple, dataclass


@dataclass(frozen=True)
class IPv4SocketAddress:
    """
    Dataclass for storing IPv4 socket addresses
    This is the combination of a 4 byte IP address
    and the port it uses
    ip_address: Address given as a string
        (e.g. "198.162.0.1")
        No support for addresses as ints
    port: Just port number as an int
    """

    ip_address: str
    port: int

    def __str__(self):
        return self.ip_address + ":" + str(self.port)


@dataclass(frozen=True)
class ObjectIdentifier:
    """
    Combination of object type and instance to indentify
    a specific object in a device
    object_type: self explanatory
        (e.g. "analog-output")
    object_instance: Instance number for that object
        usually increment from 0 for each device
    """

    object_type: str
    object_instance: int

    def to_tuple(self):
        return astuple(self)


@dataclass(frozen=True)
class SubscriptionID:
    """
    dataclass for identifying a specific bacnet object to subscribe to
    socket_address: IPv4SocketAddress dataclass object
        IP of device in combination with the port it is using for
        bacnet communication (usually 47808)
    object_key: To identify the object of the device you want to
        subscribe to
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
