from collections.abc import Callable

from BAC0 import Base, lite
from BAC0.core.functions.CoV import COVSubscription
from bacpypes3.service.cov import SubscriptionContextManager

from fastcs_bacnet.practical.BAC0.subscription_status import SubscriptionStatus, Team


class CovTracker:
    bacnet_client: lite
    team: Team
    status: SubscriptionStatus

    def __init__(
        self, bacnet_client: lite, team: Team, subscription_status: SubscriptionStatus
    ):
        self.bacnet_client = bacnet_client
        self.team = team
        self.status = subscription_status

    def start_cov(self):
        pass

    def stop_cov(self):
        pass

    def retry_cov(self):
        pass

    def callback_race(self):
        pass


def get_last_cov_task() -> COVSubscription:
    # get last tasks process ID
    cov_pid = Base._last_cov_identifier  # noqa: SLF001
    # Get object from Base dictionary
    task: COVSubscription = Base._running_cov_tasks[cov_pid]  # noqa: SLF001
    return task


async def set_cov_resubscribe_callback(
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
