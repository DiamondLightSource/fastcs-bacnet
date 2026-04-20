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

    def is_team_up(self, team: Team) -> bool:
        return team.value in self.status.value

    def set_team_up(self, team: Team, up: bool = True):
        if self.is_team_up(team) == up:
            if up:
                print(team, " is already up")
            else:
                print(team, " is already down")
            return

        if up:
            self.status = Status(order(self.status.value + team.value))
        else:
            self.status = Status(self.status.value.replace(team.value, ""))

        if self.status == Status.BOTH:
            # prepared for a race
            self.callback_called = Status.BOTH
        else:
            # no race since only one / neither is up
            self.callback_called = Status.NEITHER

    def get_status(self) -> Status:
        return self.status

    def get_callback_called(self) -> Status:
        return self.callback_called


def team_to_status(team: Team) -> Status:
    if team == Team.RED:
        return Status.RED_UP
    return Status.BLUE_UP


def get_oposite_team(team: Team) -> Team:
    if team == Team.RED:
        return Team.BLUE
    return Team.RED


def order(string: str) -> str:
    if string == "BR":
        return "RB"
    return string
