import asyncio

from fastcs.launch import FastCS
from fastcs.transports.epics import EpicsIOCOptions
from fastcs.transports.epics.ca import EpicsCATransport

from fastcs_bacnet.dummy.FastCS.subscription_device_controller import (
    SubscriptionDeviceController,
)
from fastcs_bacnet.dummy.generic.device import Device as GenericDevice


async def async_function():
    dummy_device = GenericDevice(
        "dummy",
        number_of_constant_fields=10,
        number_of_oscillating_fields=20,
        number_of_random_fields=5,
        number_of_read_write_fields=5,
    )

    epics_ca = EpicsCATransport(epicsca=EpicsIOCOptions(pv_prefix="DEMO"))

    controller = SubscriptionDeviceController(dummy_device)
    fastcs = FastCS(controller, [epics_ca])

    asyncio.create_task(fastcs.serve())

    while True:
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(async_function())
