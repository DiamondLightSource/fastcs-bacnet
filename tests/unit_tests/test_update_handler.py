import asyncio
from collections.abc import Callable

from fastcs_bacnet.practical.BAC0.subscriptions.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)
from fastcs_bacnet.practical.BAC0.subscriptions.subscription_status import (
    Status,
    SubscriptionStatus,
    Team,
)
from fastcs_bacnet.practical.BAC0.subscriptions.update_handler import (
    UpdateHandler,
)
from fastcs_bacnet.practical.generic.callback_stack import CallbackStack


def blank_update_handler_with_callback_counter(
    blank_update_callback: Callable[[], bool],
):
    callback_stack = CallbackStack[str, float]()
    callback_counter = [0]

    def callback(property_identifier: str, property_value: float):
        callback_counter[0] += 1

    callback_stack.add_to_stack(callback)

    subscription_id = SubscriptionID(
        IPv4SocketAddress("127.0.0.1", 47808), ObjectIdentifier("analog-output", 0)
    )
    status = SubscriptionStatus(callback_stack, subscription_id, 60)

    update_handler = UpdateHandler(Team.BLUE, status, blank_update_callback)

    return (update_handler, callback_counter)


async def call_callback_and_check_result(
    update_handler: UpdateHandler,
    callback_counter: list[int],
    expected_pointer_value: int,
    expected_status: Status,
):
    update_handler.callback("present-value", 0)

    # have to wait as callback creates a task
    await asyncio.sleep(0.5)

    # should not have changed as there was no race
    assert update_handler.status.get_callback_called() == expected_status

    # callback should have been called
    assert callback_counter[0] == expected_pointer_value


def test_single_update_callback():

    update_handler, callback_counter = blank_update_handler_with_callback_counter(
        lambda: False
    )
    status = update_handler.status

    # shoudnt matter but just making sure for future updates
    status.set_team_up(Team.BLUE)

    # already tested but a necessary start for this test
    assert status.get_callback_called() == Status.NEITHER

    # when update_handler.callback is called, counter should be incremented by 1
    # and Status should stay as NEITHER
    asyncio.run(
        call_callback_and_check_result(
            update_handler, callback_counter, 1, Status.NEITHER
        )
    )


def test_expect_blank_without_callback():
    update_handler, callback_counter = blank_update_handler_with_callback_counter(
        lambda: False
    )
    status = update_handler.status

    # shoudnt matter but just making sure for future updates
    status.set_team_up(Team.BLUE)

    update_handler.expect_blank_update()

    # when update_handler.callback is called, counter should be NOT incremented by 1
    # This is because a blank update was expected and the
    # blank_update_callback returns False
    # and Status should stay as NEITHER
    asyncio.run(
        call_callback_and_check_result(
            update_handler, callback_counter, 0, Status.NEITHER
        )
    )


def test_expect_blank_with_callback():
    update_handler, callback_counter = blank_update_handler_with_callback_counter(
        lambda: True
    )
    status = update_handler.status

    # shoudnt matter but just making sure for future updates
    status.set_team_up(Team.BLUE)

    update_handler.expect_blank_update()

    # when update_handler.callback is called, counter should be incremented by 1
    # This is because a blank update was expected and the
    # blank_update_callback returns True
    # and Status should stay as NEITHER
    asyncio.run(
        call_callback_and_check_result(
            update_handler, callback_counter, 1, Status.NEITHER
        )
    )


def test_one_at_a_time():
    update_handler_blue, callback_counter = blank_update_handler_with_callback_counter(
        lambda: False
    )
    status = update_handler_blue.status

    update_handler_red = UpdateHandler(Team.RED, status, lambda: False)

    # need to both be up so status is prepared for a race
    status.set_team_up(Team.BLUE)
    status.set_team_up(Team.RED)

    # callback should be called as blue "won" the race (counter === 1)
    # callback status should also reflect blue won the race
    asyncio.run(
        call_callback_and_check_result(
            update_handler_blue, callback_counter, 1, Status.BLUE_UP
        )
    )

    # callback should not be called again as it was already called
    # callback status should be reset for the next race
    asyncio.run(
        call_callback_and_check_result(
            update_handler_red, callback_counter, 1, Status.BOTH
        )
    )


def test_race():
    update_handler_blue, callback_counter = blank_update_handler_with_callback_counter(
        lambda: False
    )
    status = update_handler_blue.status

    update_handler_red = UpdateHandler(Team.RED, status, lambda: False)

    # need to both be up so status is prepared for a race
    status.set_team_up(Team.BLUE)
    status.set_team_up(Team.RED)

    async def call_callbacks_simultaneously():
        update_handler_blue.callback("present-value", 0)
        update_handler_red.callback("present-value", 0)

        # have to wait as callback creates a task
        await asyncio.sleep(0.5)

        # callback should have been called once
        assert callback_counter[0] == 1

        # status should be reset for the next race
        assert status.get_callback_called() == Status.BOTH

    asyncio.run(call_callbacks_simultaneously())


def test_stop_update_handler():
    update_handler, callback_counter = blank_update_handler_with_callback_counter(
        lambda: False
    )
    status = update_handler.status

    # shoudnt matter but just making sure for future updates
    status.set_team_up(Team.BLUE)

    update_handler.stop_cov()

    # already tested but a necessary start for this test
    assert status.get_callback_called() == Status.NEITHER

    # callback should not be called as its been stooped
    asyncio.run(
        call_callback_and_check_result(
            update_handler, callback_counter, 0, Status.NEITHER
        )
    )
