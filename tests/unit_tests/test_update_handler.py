import asyncio

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


def test_single_update_callback():

    callback_stack = CallbackStack[str, float]()
    callback_pointer = ["Not Called"]

    def callback(property_identifier: str, property_value: float):
        callback_pointer[0] = "Called"

    callback_stack.add_to_stack(callback)

    subscription_id = SubscriptionID(
        IPv4SocketAddress("127.0.0.1", 47808), ObjectIdentifier("analog-output", 0)
    )
    status = SubscriptionStatus(callback_stack, subscription_id, 60)

    update_handler = UpdateHandler(Team.BLUE, status, lambda: False)

    # shoudnt matter but just making sure for future updates
    status.set_team_up(Team.BLUE)

    # already tested but a necessary start for this test
    assert status.get_callback_called() == Status.NEITHER

    async def run_callback_and_check_result():
        update_handler.callback("present-value", 0)

        # have to wait as callback creates a task
        await asyncio.sleep(0.5)

        # should not have changed as there was no race
        assert status.get_callback_called() == Status.NEITHER

        # callback should have been called
        assert callback_pointer[0] == "Called"

    asyncio.run(run_callback_and_check_result())


def test_expect_blank_without_callback():
    callback_stack = CallbackStack[str, float]()
    callback_pointer = ["Not Called"]

    def callback(property_identifier: str, property_value: float):
        callback_pointer[0] = "Called"

    callback_stack.add_to_stack(callback)

    subscription_id = SubscriptionID(
        IPv4SocketAddress("127.0.0.1", 47808), ObjectIdentifier("analog-output", 0)
    )
    status = SubscriptionStatus(callback_stack, subscription_id, 60)

    def blank_update_callback():
        return False

    update_handler = UpdateHandler(Team.BLUE, status, blank_update_callback)

    update_handler.expect_blank_update()

    # shoudnt matter but just making sure for future updates
    status.set_team_up(Team.BLUE)

    async def run_callback_and_check_result():
        update_handler.callback("present-value", 0)

        # have to wait as callback creates a task
        await asyncio.sleep(0.5)

        # callback should NOT have been called as it was a blank update
        # AND the blank callback returned False
        assert callback_pointer[0] == "Not Called"

    asyncio.run(run_callback_and_check_result())


def test_expect_blank_with_callback():
    callback_stack = CallbackStack[str, float]()
    callback_pointer = ["Not Called"]

    def callback(property_identifier: str, property_value: float):
        callback_pointer[0] = "Called"

    callback_stack.add_to_stack(callback)

    subscription_id = SubscriptionID(
        IPv4SocketAddress("127.0.0.1", 47808), ObjectIdentifier("analog-output", 0)
    )
    status = SubscriptionStatus(callback_stack, subscription_id, 60)

    update_handler = UpdateHandler(Team.BLUE, status, lambda: True)

    update_handler.expect_blank_update()

    # shoudnt matter but just making sure for future updates
    status.set_team_up(Team.BLUE)

    async def run_callback_and_check_result():
        update_handler.callback("present-value", 0)

        # have to wait as callback creates a task
        await asyncio.sleep(0.5)

        # callback should have been called as it was a blank update
        # AND the blank callback returned True
        assert callback_pointer[0] == "Called"

    asyncio.run(run_callback_and_check_result())


def test_one_at_a_time():
    callback_stack = CallbackStack[str, float]()
    callback_pointer = ["Not Called"]

    def callback(property_identifier: str, property_value: float):
        if callback_pointer[0] == "Not Called":
            callback_pointer[0] = "Called"
        elif callback_pointer[0] == "Called":
            callback_pointer[0] = "Called Twice"

    callback_stack.add_to_stack(callback)

    subscription_id = SubscriptionID(
        IPv4SocketAddress("127.0.0.1", 47808), ObjectIdentifier("analog-output", 0)
    )
    status = SubscriptionStatus(callback_stack, subscription_id, 60)

    update_handler_blue = UpdateHandler(Team.BLUE, status, lambda: False)
    update_handler_red = UpdateHandler(Team.RED, status, lambda: False)

    # need to both be up so status is prepared for a race
    status.set_team_up(Team.BLUE)
    status.set_team_up(Team.RED)

    async def call_callbacks_one_at_a_time():
        update_handler_blue.callback("present-value", 0)

        # have to wait as callback creates a task
        await asyncio.sleep(0.5)

        assert callback_pointer[0] == "Called"

        # status should reflect that blue got their first
        assert status.get_callback_called() == Status.BLUE_UP

        update_handler_red.callback("present-value", 0)

        # have to wait as callback creates a task
        await asyncio.sleep(0.5)

        # callback should not have been called again
        assert callback_pointer[0] == "Called"

        # status should be reset for the next race
        assert status.get_callback_called() == Status.BOTH

    asyncio.run(call_callbacks_one_at_a_time())


def test_race():
    callback_stack = CallbackStack[str, float]()
    callback_pointer = ["Not Called"]

    def callback(property_identifier: str, property_value: float):
        if callback_pointer[0] == "Not Called":
            callback_pointer[0] = "Called"
        elif callback_pointer[0] == "Called":
            callback_pointer[0] = "Called Twice"

    callback_stack.add_to_stack(callback)

    subscription_id = SubscriptionID(
        IPv4SocketAddress("127.0.0.1", 47808), ObjectIdentifier("analog-output", 0)
    )
    status = SubscriptionStatus(callback_stack, subscription_id, 60)

    update_handler_blue = UpdateHandler(Team.BLUE, status, lambda: False)
    update_handler_red = UpdateHandler(Team.RED, status, lambda: False)

    # need to both be up so status is prepared for a race
    status.set_team_up(Team.BLUE)
    status.set_team_up(Team.RED)

    async def call_callbacks_one_at_a_time():
        update_handler_blue.callback("present-value", 0)
        update_handler_red.callback("present-value", 0)

        # have to wait as callback creates a task
        await asyncio.sleep(0.5)

        # callback should have been called once
        assert callback_pointer[0] == "Called"

        # status should be reset for the next race
        assert status.get_callback_called() == Status.BOTH

    asyncio.run(call_callbacks_one_at_a_time())


def test_stop_update_handler():
    callback_stack = CallbackStack[str, float]()
    callback_pointer = ["Not Called"]

    def callback(property_identifier: str, property_value: float):
        callback_pointer[0] = "Called"

    callback_stack.add_to_stack(callback)

    subscription_id = SubscriptionID(
        IPv4SocketAddress("127.0.0.1", 47808), ObjectIdentifier("analog-output", 0)
    )
    status = SubscriptionStatus(callback_stack, subscription_id, 60)

    update_handler = UpdateHandler(Team.BLUE, status, lambda: False)

    # shoudnt matter but just making sure for future updates
    status.set_team_up(Team.BLUE)

    update_handler.stop_cov()

    # already tested but a necessary start for this test
    assert status.get_callback_called() == Status.NEITHER

    async def run_callback_and_check_result():
        update_handler.callback("present-value", 0)

        # have to wait as callback creates a task
        await asyncio.sleep(0.5)

        # should not have changed as there was no race
        assert status.get_callback_called() == Status.NEITHER

        # callback should have been called
        assert callback_pointer[0] == "Not Called"

    asyncio.run(run_callback_and_check_result())
