from dataclasses import dataclass

from fastcs.attributes import AttributeIO, AttributeIORef, AttrR, AttrRW, AttrW
from fastcs.controllers.controller import Controller
from fastcs.datatypes import Float

from fastcs_bacnet.dummy.generic.device import Device as GenericDevice
from fastcs_bacnet.dummy.generic.device_variables.device_variable import DeviceVariable
from fastcs_bacnet.dummy.generic.device_variables.read_write_variable import (
    ReadWriteVariable,
)


@dataclass
class GenericVariableAttributeIORef(AttributeIORef):
    name: str
    variable_type: type[DeviceVariable]


class GenericVariableAttributeIO(AttributeIO[float, GenericVariableAttributeIORef]):
    def __init__(self, device: GenericDevice):
        self.device = device

    async def update(self, attr: AttrR[float, GenericVariableAttributeIORef]):

        await attr.update(self.device.get_variable(attr.io_ref.name).get_value())

    async def send(
        self, attr: AttrW[float, GenericVariableAttributeIORef], value: float
    ):
        variable = self.device.get_variable(attr.io_ref.name)
        if type(variable) is ReadWriteVariable:
            variable.set_value(value)


class PollingDeviceController(Controller):
    def __init__(self, device: GenericDevice):
        super().__init__(ios=[GenericVariableAttributeIO(device)])

        for variable_name, variable_type in device.get_variable_summary():
            variable_reference = GenericVariableAttributeIORef(
                variable_name, variable_type, update_period=0.2
            )

            if variable_type is ReadWriteVariable:
                attribute = AttrRW(Float(), variable_reference)
            else:
                attribute = AttrR(Float(), variable_reference)

            self.add_attribute(variable_name, attribute)
