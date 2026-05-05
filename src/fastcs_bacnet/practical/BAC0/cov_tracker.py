import asyncio
from collections.abc import Callable

from BAC0 import Base, lite
from BAC0.core.functions.CoV import COVSubscription
from bacpypes3.service.cov import SubscriptionContextManager

from fastcs_bacnet.practical.BAC0.subscription_status import (
    Status,
    SubscriptionStatus,
    Team,
    get_oposite_team,
    team_to_status,
)


class CovTracker:
    bacnet_client: lite
    team: Team
    status: SubscriptionStatus

    cov_task: COVSubscription | None = None

    subscription_confirmed: bool = False
    cov_stopped: bool = False

    def __init__(
        self, bacnet_client: lite, team: Team, subscription_status: SubscriptionStatus
    ):
        """
        bacnet_client: BAC0 isntance used to start subscriptions
        team: cov_trackers come in pairs, team is either red or blue
            its partner should have the oposite team
        """
        self.bacnet_client = bacnet_client
        self.team = team
        self.status = subscription_status

    def start_cov(self):
        """
        Sends CoV request
        Cleans up previous CoV request (if it exists)
        And sets the callback that validates CoV requests
        Does NOT change SubscriptionStatus
        """

        # clean up previous cov task before starting a new one
        # Maybe turn this into a method??
        if self.cov_task is not None:
            self.bacnet_client.cancel_cov(self.cov_task.process_identifier)
            self.cov_task = None

        self.on_resubscribe()

        self.bacnet_client.cov(
            str(self.status.subscription_id.socket_address),
            self.status.subscription_id.object_key.to_tuple(),
            self.status.lifetime,
            callback=self.callback(),
        )

        self.cov_task = get_last_cov_task()

        set_cov_resubscribe_callback(
            self.bacnet_client, self.cov_task, self.on_resubscribe
        )

    def stop_cov(self):
        """
        Sets the cov_stopped attribute to True
        Updates status
        Clean up CoV
        """
        self.cov_stopped = True

        # Update status
        if self.status.is_team_up(self.team):
            self.status.set_team_up(self.team, False)

        # Clean up the CoV that has been cancelled
        if self.cov_task is not None:
            self.bacnet_client.cancel_cov(self.cov_task.process_identifier)
            self.cov_task = None

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

    def on_resubscribe_fail(self):
        """
        Should only be called when a cov request (or resubscription from a cov request)
        is sent out and not responded to (response would look like an update but has
        the same value as the last update or is in its deadband)
        Updates status
        Cleans up failed CoV request if it exists
        Will try to restart in phase if other team is still up
        """
        # CoV request was never responded to

        # Update status
        if self.status.is_team_up(self.team):
            self.status.set_team_up(self.team, False)

        # Clean up the CoV that failed
        if self.cov_task is not None:
            self.bacnet_client.cancel_cov(self.cov_task.process_identifier)
            self.cov_task = None

        # If the other team is up, try again in lifetime
        # (can be fancier with scheduling if we use the start time of other CoV)
        def try_subscription_again():
            if self.status.is_team_up(get_oposite_team(self.team)):
                self.start_cov()

        asyncio.get_running_loop().call_later(
            self.status.lifetime, try_subscription_again
        )

    def on_resubscribe(self):
        """
        Set as the CoV resubscribe callback
        Also call when manually restarting the subscription (start method)
        Checks if the subscription is restarted correctly
        """

        async def on_resubscribe_task():
            self.subscription_confirmed = False

            await asyncio.sleep(7)

            if not self.subscription_confirmed:
                self.on_resubscribe_fail()

        asyncio.create_task(on_resubscribe_task())


def get_last_cov_task() -> COVSubscription:
    """
    Gets the most recent async task that was created from a cov request
    from the BAC0 Base class
    """
    # get last tasks process ID
    cov_pid = Base._last_cov_identifier  # noqa: SLF001
    # Get object from Base dictionary
    task: COVSubscription = Base._running_cov_tasks[cov_pid]  # noqa: SLF001
    return task


def set_cov_resubscribe_callback(
    bacnet_client: lite, task: COVSubscription, func: Callable[[], None]
):
    """
    Sets the function that is called when a cov is automatically refreshed
    """
    scm_key = (task.address, task.process_identifier)

    def on_cov_subscription_start(_):
        subscription_context_manager: SubscriptionContextManager = (
            bacnet_client.this_application.app._cov_contexts[  # noqa: SLF001
                scm_key
            ]
        )

        def decorate(coroutine):
            async def new_coroutine(*args):
                func()

                await coroutine(*args)

            return new_coroutine

        subscription_context_manager.refresh_subscription = decorate(
            subscription_context_manager.refresh_subscription
        )

    if task.task is not None:
        # only run once the CoV task has actually been started
        # otherwise subscription context manager will not have been created yet
        task.task.add_done_callback(on_cov_subscription_start)
