from dataclasses import dataclass


@dataclass(frozen=True)
class SubscriptionID:
    address: str
    port: int
    object_type: str
    object_id: int
