import asyncio

from fastcs.attributes import AttrR, AttrRW
from fastcs.controllers.controller import Controller
from fastcs.datatypes import Float
from fastcs.util import ONCE

from fastcs_bacnet.dummy.FastCS.polling_device_controller import (
    GenericVariableAttributeIO,
    GenericVariableAttributeIORef,
)
from fastcs_bacnet.dummy.generic.device import Device as GenericDevice
from fastcs_bacnet.dummy.generic.device_variables.read_write_variable import (
    ReadWriteVariable,
)


class GenericVariableSubscriptionAttributeIO(GenericVariableAttributeIO):
    async def update(self, attr: AttrR[float, GenericVariableAttributeIORef]):

        # set initial value
        await attr.update(self.device.get_variable(attr.io_ref.name).get_value())

        def actual_update(new_value: float, old_value: float | None):
            asyncio.create_task(attr.update(new_value))

        self.device.get_variable(attr.io_ref.name).callback_stack.add_to_stack(
            actual_update
        )


class SubscriptionDeviceController(Controller):
    def __init__(self, device: GenericDevice):
        super().__init__(ios=[GenericVariableSubscriptionAttributeIO(device)])

        for variable_name, variable_type in device.get_variable_summary():
            variable_reference = GenericVariableAttributeIORef(
                variable_name, variable_type, update_period=ONCE
            )

            if variable_type is ReadWriteVariable:
                attribute = AttrRW(Float(), variable_reference)
            else:
                attribute = AttrR(Float(), variable_reference)

            self.add_attribute(variable_name, attribute)
