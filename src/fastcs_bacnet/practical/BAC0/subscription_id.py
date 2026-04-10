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
