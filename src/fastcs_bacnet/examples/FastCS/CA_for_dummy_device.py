from fastcs.controllers.controller import Controller
from fastcs.launch import FastCS
from fastcs.transports.epics import EpicsIOCOptions
from fastcs.transports.epics.ca import EpicsCATransport
from softioc.imports import callbackSetQueueSize

from fastcs_bacnet.dummy_device import DummyDevice
from fastcs_bacnet.dummy_device_controller import DummyDeviceController


def start_fastcs_ca_with_controller(controller: Controller):
    epics_ca = EpicsCATransport(epicsca=EpicsIOCOptions(pv_prefix="DEMO"))
    fastcs = FastCS(controller, [epics_ca])
    # increases the number of attributes allowed
    callbackSetQueueSize(16000)
    fastcs.run()


def single_controller_multi_constants():
    dummy_device = DummyDevice(number_of_constant_fields=15000)
    dummy_controller = DummyDeviceController(dummy_device)

    start_fastcs_ca_with_controller(dummy_controller)
