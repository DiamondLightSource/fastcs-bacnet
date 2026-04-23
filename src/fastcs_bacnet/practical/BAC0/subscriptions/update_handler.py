import asyncio
from collections.abc import Callable

from fastcs_bacnet.practical.BAC0.subscriptions.subscription_status import (
    Status,
    SubscriptionStatus,
    Team,
    get_oposite_team,
    team_to_status,
)


class UpdateHandler:
    """
    CoV updates come through this object via the callback method
    it is responsible for processing them
    """

    status: SubscriptionStatus
    team: Team
    cov_stopped: bool = False
    # A "blank update" is a update that tells us nothing
    # The value recieved is in the deadband of the previous value
    # You may be thinking that we should never recieve these updates
    # However, an update like this will be recieved when a CoV is restarted
    blank_update_expected: bool = False
    blank_update_callback: Callable[[], bool]

    running_async_tasks: set[asyncio.Task]

    def __init__(
        self,
        team: Team,
        status: SubscriptionStatus,
        subscription_confirmation_callback: Callable[[], bool],
    ):
        self.team = team
        self.status = status
        self.blank_update_callback = subscription_confirmation_callback

        self.running_async_tasks = set()

    def callback(self, property_identifier: str, property_value: float):
        """
        The callback function that should be used in the cov request
        Starts a callback race with the other team
        Returns if cov has been stopped
        Also doesnt run the callback race if the update is a response to renewing the
        subscription
        """

        print("entering update handler callback!!")

        if self.cov_stopped:
            return

        # If we are expecting a blank update we just assume the next update we get is
        # a blank one. This is not good
        # TODO: At LEAST add a time for when the blank update was expected
        # if the next update is recieved too long after the time (1 second) assume we
        # missed the blank update and maybe call a callback??
        # TODO: Better implementation (but more technical) check if the update is in the
        # deadband or not. This may require more reads and therefore network traffic
        # but it would be good to be sure
        if self.blank_update_expected:
            self.blank_update_expected = False

            # If subscription confirmation callback returns True, run the callback race
            # Otherwise just return
            # It doesnt count as a proper update as its just to validate the
            # subscription
            if not self.blank_update_callback():
                return

        task = asyncio.create_task(
            self.callback_race(property_identifier, property_value)
        )
        self.running_async_tasks.add(task)
        task.add_done_callback(self.running_async_tasks.discard)

    async def callback_race(self, property_identifier: str, property_value: float):
        """
        "Races" the other team to call the callback stack first
        Ensures the callback stack is only run once per update even though we
        run 2 CoVs in parallel
        Both CoVs share a status object, the first to recieve the update uses its lock,
        sets the callback called status and calls the callback stack
        The second is locked out until the first finishes, when its let in it can see
        the status has been updated by the other team so it updates it back and does not
        call the callback stack
        If one cov_tracker is down no race occurs and the stack is called as normal
        """

        async with self.status.callback_lock:
            # This team has won the race already and got another CoV??
            # This is an error state
            # TODO: Throw an appropriate error here
            if self.status.callback_called == team_to_status(self.team):
                print("this should not happen, something has gone wrong")
                return

            # Other team won race
            # Dont call callback as it has already been called
            elif self.status.callback_called == team_to_status(
                get_oposite_team(self.team)
            ):
                # reseting state for the next race
                self.status.callback_called = Status.BOTH
                return

            # This team won the race
            if self.status.callback_called == Status.BOTH:
                self.status.callback_called = team_to_status(self.team)
                # TODO: Create a task here to check the other team recieves a CoV aswell

            # If status was BOTH or NEITHER we call the callback
            # Either there is nothing to race (only one CoV up)
            # OR this team won the race

            self.status.callback.sum_callback(property_identifier, property_value)

    def expect_blank_update(self):
        self.blank_update_expected = True

    def stop_cov(self):
        self.cov_stopped = True
