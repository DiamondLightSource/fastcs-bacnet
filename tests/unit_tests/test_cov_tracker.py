import asyncio
import socket

from BAC0 import start

from conftest import get_multiprocessing_context
from fastcs_bacnet.dummy.BAC0.analog_output_object import AnalogOutputObject
from fastcs_bacnet.dummy.generic.device_variables.read_write_variable import (
    ReadWriteVariable,
)
from fastcs_bacnet.practical.BAC0.subscriptions.cov_tracker import (
    CovTracker,
)
from fastcs_bacnet.practical.BAC0.subscriptions.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)
from fastcs_bacnet.practical.BAC0.subscriptions.subscription_status import (
    SubscriptionStatus,
    Team,
)
from fastcs_bacnet.practical.generic.callback_stack import CallbackStack

COV_LIFETIME = 15


def start_bacnet_object_wrapper(context):

    async def start_bacnet_object():
        async with start() as bac0_device:
            read_write_variable = ReadWriteVariable("read_write_variable")

            AnalogOutputObject(
                bac0_device, "read_write_object", "", 0, read_write_variable
            )

            await asyncio.sleep(30)

            # async def take_updates():
            #     while True:
            #         new_value = float(context.recv())
            #         read_write_variable.set_value(new_value)

            # asyncio.create_task(take_updates())

    asyncio.run(start_bacnet_object())


def set_up_bacnet_object_context():
    context = get_multiprocessing_context()

    dummy_object_context, bacnet_clinet_context = context.Pipe()

    dummy_object_process = context.Process(
        target=start_bacnet_object_wrapper, args=[dummy_object_context]
    )

    dummy_object_process.start()

    return bacnet_clinet_context


async def set_up_cov_tracker():

    callback_counter = [0]

    def callback(property_identifier: str, property_value: float):
        print("calling callback!!")
        callback_counter[0] += 1

    device_address = IPv4SocketAddress(
        socket.gethostbyname(socket.gethostname()), 47808
    )
    object_key = ObjectIdentifier("analog-output", 0)

    subscription_list = [SubscriptionID(device_address, object_key)]

    async with start(port=47809) as bacnet_client:
        callback_stack = CallbackStack()
        callback_stack.add_to_stack(callback)

        subscription_status = SubscriptionStatus(
            callback_stack, subscription_list[0], COV_LIFETIME
        )

        cov_tracker = CovTracker(bacnet_client, Team.BLUE, subscription_status)

        return (cov_tracker, callback_counter)


def test_cov_callback_count():
    print("starting!!")
    context = set_up_bacnet_object_context()
    print("bacnet object set up!!")

    async def run_counter_tests():
        print("in async")
        cov_tracker, callback_counter = await set_up_cov_tracker()

        await asyncio.sleep(5)

        # cov hasnt even started yet, callback should not have been called
        assert callback_counter[0] == 0

        cov_tracker.start_cov()

        print("cov started")
        await asyncio.sleep(1.0)

        # callback should be called ONCE when cov is started
        # even though its a blank update
        assert callback_counter[0] == 1

        context.send("5.0")

        await asyncio.sleep(0.1)

        # Callback should be called again on value change
        assert callback_counter[0] == 2

        # lifetime of cov is COV_LIFETIME seconds
        # wait until a new one has been sent out
        await asyncio.sleep(COV_LIFETIME)

        # callback counter should NOT have changed
        # new cov will have sent a blank update but this
        # should NOT have triggered a callback
        assert callback_counter[0] == 2

        context.send("7.0")

        await asyncio.sleep(0.1)

        # Make sure new cov is working
        assert callback_counter[0] == 3

    asyncio.run(run_counter_tests())
