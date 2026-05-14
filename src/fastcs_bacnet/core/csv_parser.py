from fastcs_bacnet.core.exceptions import InvalidFileFormat
from fastcs_bacnet.practical.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)


def parse_csv(filepath: str) -> list[SubscriptionID]:
    """
    Creates a list of SubscriptionID s from an EDE file
    """

    subscription_ids: list[SubscriptionID] = []

    # escalates file not found exception
    with open(filepath) as file:
        for line in file:
            cells = line.split(", ")
            try:
                socket_address = IPv4SocketAddress(cells[0], int(cells[1]))
                object_id = ObjectIdentifier(cells[2], int(cells[3]))
                subscription_ids.append(SubscriptionID(socket_address, object_id))
            except BaseException:
                raise InvalidFileFormat(
                    "Couldnt convert row to a SubscriptionID: \n" + line
                ) from BaseException

    if len(subscription_ids) == 0:
        raise InvalidFileFormat("File must have at least one valid SubscriptionID row")

    return subscription_ids
