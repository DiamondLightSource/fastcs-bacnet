import csv

from fastcs_bacnet.practical.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)


class InvalidFileFormat(BaseException):
    pass


def parse_csv(filepath: str) -> list[SubscriptionID]:
    """
    Creates a list of SubscriptionID s from an EDE file
    """

    subscription_ids: list[SubscriptionID] = []

    # escalates file not found exception
    with open(filepath) as file:
        reader = csv.DictReader(
            file,
            ["ip_address", "port", "object_type", "object_instance"],
            skipinitialspace=True,
        )
        for line in reader:
            try:
                socket_address = IPv4SocketAddress(
                    line["ip_address"], int(line["port"])
                )
                object_id = ObjectIdentifier(
                    line["object_type"], int(line["object_instance"])
                )
                subscription_ids.append(SubscriptionID(socket_address, object_id))
            except BaseException:
                raise InvalidFileFormat(
                    "Couldnt convert row to a SubscriptionID: \n" + str(line)
                ) from BaseException

    if len(subscription_ids) == 0:
        raise InvalidFileFormat("File must have at least one valid SubscriptionID row")

    return subscription_ids
