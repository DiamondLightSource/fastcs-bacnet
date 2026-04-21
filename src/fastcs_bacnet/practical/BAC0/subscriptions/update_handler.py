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
    subscription_confirmation_callback: Callable[[], None]

    def __init__(
        self,
        team: Team,
        status: SubscriptionStatus,
        subscription_confirmation_callback: Callable[[], None],
    ):
        self.team = team
        self.status = status
        self.subscription_confirmation_callback = subscription_confirmation_callback

    async def callback(self):
        """
        The callback function that should be used in the cov request
        Starts a callback race with the other team
        Returns if cov has been stopped
        Also doesnt run the callback race if the update is a response to renewing the
        subscription
        """
        if self.cov_stopped:
            return

        # CoV updates can be the initial subscription notification
        # In this case we DONT want to call the callback as there has been
        # no actual update
        # UNLESS its the very first subscription we get from this ID
        # TODO: Add check mentioned above
        if not self.subscription_confirmed:
            self.subscription_confirmed = True

            if not self.status.is_team_up(self.team):
                self.status.set_team_up(self.team, True)
            return

        await self.callback_race()

    async def callback_race(self):
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

            self.status.callback.sum_callback()
