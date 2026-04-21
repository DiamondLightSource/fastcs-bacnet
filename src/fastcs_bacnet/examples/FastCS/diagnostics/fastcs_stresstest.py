import asyncio

from fastcs.launch import FastCS
from fastcs.transports.epics import EpicsIOCOptions
from fastcs.transports.epics.ca import EpicsCATransport
from softioc.imports import callbackSetQueueSize

from fastcs_bacnet.dummy.FastCS.subscription_device_controller import (
    SubscriptionDeviceController,
)
from fastcs_bacnet.dummy.generic.device import Device as GenericDevice


async def async_function():
    dummy_device = GenericDevice(
        "dummy",
        number_of_random_fields=15000,
    )

    dummy_device.get_variable("dummy_random_477").callback_stack.add_to_stack(
        lambda x, y: print("new value: ", y)
    )

    callbackSetQueueSize(30000)

    epics_ca = EpicsCATransport(epicsca=EpicsIOCOptions(pv_prefix="DEMOONETWOONE"))

    controller = SubscriptionDeviceController(dummy_device)
    fastcs = FastCS(controller, [epics_ca])

    asyncio.create_task(fastcs.serve())

    while True:
        await asyncio.sleep(10)


asyncio.run(async_function())
