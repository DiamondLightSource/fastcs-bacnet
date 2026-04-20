from asyncio import Lock
from enum import Enum

from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID
from fastcs_bacnet.practical.generic.callback_stack import CallbackStack


class Status(Enum):
    NEITHER = ""
    RED_UP = "R"
    BLUE_UP = "B"
    BOTH = "RB"


class Team(Enum):
    RED = "R"
    BLUE = "B"


class SubscriptionStatus:
    subscription_id: SubscriptionID
    callback: CallbackStack
    status: Status = Status.NEITHER
    callback_called: Status = Status.NEITHER
    callback_lock: Lock
    lifetime: int

    def __init__(
        self,
        callback: CallbackStack,
        subscription_id: SubscriptionID,
        subscription_lifetime: int,
    ):
        self.callback = callback
        self.subscription_id = subscription_id
        self.lifetime = subscription_lifetime

        self.callback_lock = Lock()

    def is_red_up(self) -> bool:
        return "R" in self.status.value

    def is_blue_up(self) -> bool:
        return "B" in self.status.value

    def get_status(self) -> Status:
        return self.status

    def get_callback_called(self) -> Status:
        return self.callback_called
