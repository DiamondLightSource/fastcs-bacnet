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

    cov_task: COVSubscription

    subscription_confirmed: bool = False

    def __init__(
        self, bacnet_client: lite, team: Team, subscription_status: SubscriptionStatus
    ):
        self.bacnet_client = bacnet_client
        self.team = team
        self.status = subscription_status

    def start_cov(self):

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
        pass

    async def callback(self):

        if not self.subscription_confirmed:
            # TODO: Set status here
            self.subscription_confirmed = True
            return

        await self.callback_race()

    async def callback_race(self):

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
        # CoV request was never responded to

        # Set up status
        if self.status.is_team_up(self.team):
            self.status.set_team_up(self.team, False)

        # Clean up the CoV that failed
        self.bacnet_client.cancel_cov(self.cov_task.process_identifier)

        # If the other team is up, try again in lifetime / 2
        # (can be fancier with scheduling if we use the start time of other CoV)
        if self.status.is_team_up(get_oposite_team(self.team)):
            asyncio.get_running_loop().call_later(
                self.status.lifetime // 2, self.start_cov
            )
        # Otherwise, cancel the whole thing
        # Not sure what code this involves yet

    def on_resubscribe(self):

        async def on_resubscribe_task():
            self.subscription_confirmed = False

            await asyncio.sleep(7)

            if not self.subscription_confirmed:
                self.on_resubscribe_fail()

        asyncio.create_task(on_resubscribe_task())


def get_last_cov_task() -> COVSubscription:
    # get last tasks process ID
    cov_pid = Base._last_cov_identifier  # noqa: SLF001
    # Get object from Base dictionary
    task: COVSubscription = Base._running_cov_tasks[cov_pid]  # noqa: SLF001
    return task


def set_cov_resubscribe_callback(
    bacnet_client: lite, task: COVSubscription, func: Callable[[], None]
):
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
