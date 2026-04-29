from fastcs_bacnet.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)


def parse_csv(filepath: str) -> list[SubscriptionID]:

    subscription_ids: list[SubscriptionID] = []

    try:
        with open(filepath) as file:
            for line in file:
                cells = line.split(", ")
                try:
                    ip = IPv4SocketAddress(cells[0], int(cells[1]))
                    object_id = ObjectIdentifier(cells[2], int(cells[3]))
                    subscription_ids.append(SubscriptionID(ip, object_id))
                except BaseException:
                    print("couldnt convert row to a SubscriptionID")
                    print(line)

    except FileNotFoundError:
        print("Bad filepath")

    return subscription_ids
