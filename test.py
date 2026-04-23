import asyncio
import socket

from BAC0 import start

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


async def test():
    async with start() as bac0_device:
        async with start(port=47809) as bacnet_client:
            read_write_variable = ReadWriteVariable("read_write_variable")

            AnalogOutputObject(
                bac0_device, "read_write_object", "", 0, read_write_variable
            )

            callback_counter = [0]

            def callback(property_identifier: str, property_value: float):
                print("calling callback!!")
                callback_counter[0] += 1

            device_address = IPv4SocketAddress(
                socket.gethostbyname(socket.gethostname()), 47808
            )
            object_key = ObjectIdentifier("analog-output", 0)

            subscription_list = [SubscriptionID(device_address, object_key)]

            callback_stack = CallbackStack()
            callback_stack.add_to_stack(callback)

            subscription_status = SubscriptionStatus(
                callback_stack, subscription_list[0], COV_LIFETIME
            )

            cov_tracker = CovTracker(bacnet_client, Team.BLUE, subscription_status)
            cov_tracker.start_cov()

            await asyncio.sleep(5)
            print("slept")

            # read_write_variable.set_value(9)

            # print("value set")

            await asyncio.sleep(5)


asyncio.run(test())
