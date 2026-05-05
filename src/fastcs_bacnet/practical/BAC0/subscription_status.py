from asyncio import Lock
from enum import Enum

from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID
from fastcs_bacnet.practical.generic.callback_stack import CallbackStack


class Status(Enum):
    """
    Records the status of cov_tracker s
    """

    NEITHER = ""
    RED_UP = "R"
    BLUE_UP = "B"
    BOTH = "RB"


class Team(Enum):
    """
    Describes the team of a cov_tracker
    """

    RED = "R"
    BLUE = "B"


class SubscriptionStatus:
    """
    Stores state for an object subscription that a cov_tracker needs
    """

    subscription_id: SubscriptionID
    callback: CallbackStack
    # Represents which cov_tracker s are currently working
    status: Status = Status.NEITHER
    # Represents which cov_tracker recieves the update first
    callback_called: Status = Status.NEITHER
    # Allows one update to be processed at a time
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
        """
        Returns if the team's cov_tracker is currently working
        """
        return team.value in self.status.value

    def set_team_up(self, team: Team, up: bool = True):
        """
        Sets the status to represent if the teams cov_tracker is working
        team: cov_tracker to set the status of
        up: True if that cov_tracker is working, False is not
        """
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
    return Status(team.value)


def get_oposite_team(team: Team) -> Team:
    if team == Team.RED:
        return Team.BLUE
    return Team.RED


def order(string: str) -> str:
    """
    Literally just converts BR to RB, otherwise returns string as normal
    For when you want to change status by adding to the string
    E.g. Only blue was up before (status = "B") but now both are up
        status += "R" but BR is not a valid Status value
    Should I have just used a set??
    """
    if string == "BR":
        return "RB"
    return string
