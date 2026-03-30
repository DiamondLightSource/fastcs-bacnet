import asyncio

from fastcs.launch import FastCS
from fastcs.transports.epics import EpicsIOCOptions
from fastcs.transports.epics.ca import EpicsCATransport

from fastcs_bacnet.dummy.FastCS.polling_device_controller import PollingDeviceController
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

    controller = PollingDeviceController(dummy_device)
    fastcs = FastCS(controller, [epics_ca])

    asyncio.create_task(fastcs.serve())

    while True:
        await asyncio.sleep(10)


asyncio.run(async_function())

# NOTE: To access variables through channel access use command:
# caget DEMO:<variable name>
# Variable name convention: Dummy<Type><Instance number>
# Example: DummyOscillating18
# Types: Constant, Oscillating, Random, ReadWrite

# NOTE: To write to ReadWrite variables through channel access use command:
# caput DEMO:DummyReadWrite<instance number> <new value>
# Where <new value> is a float
