from collections import defaultdict
from dataclasses import astuple, dataclass, field


@dataclass(frozen=True)
class IPv4SocketAddress:
    """
    Dataclass for storing IPv4 socket addresses for a Bacnet device

    This is the combination of a 4 byte IP address
    and the port it uses. Also stores the device instance number of
    the device the address correlates to

    ip_address: Address given as a string
        (e.g. "198.162.0.1")
        No support for addresses as ints
    port: Just port number as an int
    device_instance: instance number for the device this IP represents
    """

    ip_address: str
    port: int
    device_instance: int

    def __str__(self):
        return f"{self.ip_address}:{self.port}"


@dataclass(frozen=True)
class ObjectIdentifier:
    """
    Dataclass for referencing a bacnet object on a specific device

    This is the combination of the object's type and instance number

    object_type: self explanatory
        (e.g. "analog-output")
    object_instance: Instance number for that object
    """

    object_type: str
    object_instance: int

    def to_tuple(self):
        return astuple(self)


@dataclass(frozen=True)
class SubscriptionID:
    """
    Dataclass for identifying a specific bacnet object on a specific device

    This is a combination of an IPv4SocketAddress to identify the device and an
    ObjectIdentifier to identify the object on that device

    socket_address: IPv4SocketAddress dataclass object
        IP of device in combination with the port it is using for
        bacnet communication (usually 47808)
    object_id: To identify the object of the device you want to
        subscribe to
    """

    socket_address: IPv4SocketAddress
    object_id: ObjectIdentifier


def sort_subscriptions(
    subscription_ids: set[SubscriptionID],
) -> dict[IPv4SocketAddress, list[SubscriptionID]]:
    """
    Sorts a list of subscription ids into lists of subscriptions grouped
    by their socket address

    A dictionary is returned that maps IPv4SocketAddress s to all SubscriptionID s
    that use that socket address

    subscription_ids: A list of SubscriptionID objects to sort
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


@dataclass
class PVNode:
    """A node of a tree structure, describing any immediate children (each of which is a
    PV) and any sub-nodes"""

    suffix: dict[str, SubscriptionID] = field(default_factory=dict)
    children: dict[str, "PVNode"] = field(default_factory=lambda: defaultdict(PVNode))


def sort_dict(pv_names_dict: dict[SubscriptionID, str]) -> dict[str, "PVNode"]:
    """Sort the input structure into a tree, where each layer of the tree is a layer of
    the EPICS PV naming convention. Each layer represents a colon delimiter."""
    # Invert dictionary as we want to group info by PV name, not by subscription ID
    inverted_dict: dict[str, SubscriptionID] = {}

    for subs_id, pv in pv_names_dict.items():
        if pv in inverted_dict:
            raise ValueError(f"Duplicate PV name {pv} detected")
        inverted_dict[pv] = subs_id

    root_node = PVNode()

    for k, v in inverted_dict.items():
        parts = k.split(":")

        node = root_node

        # The last element is the PV name
        for part in parts[:-1]:
            node = node.children[part]

        # In theory this will never be hit, due to the checks done when inverting the
        # dictionary above, but this protects us if we ever change the input data
        # structure
        assert parts[-1] not in node.suffix
        node.suffix[parts[-1]] = v

    return root_node.children
