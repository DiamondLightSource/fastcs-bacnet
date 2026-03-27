from fastcs.attributes import AttributeIO, AttributeIORef, AttrR, AttrW
from fastcs.controllers.controller import Controller

from fastcs_bacnet.dummy.generic.device import Device as GenericDevice
from fastcs_bacnet.dummy.generic.device_variables.device_variable import DeviceVariable


class GenericVariableAttributeIORef(AttributeIORef):
    name: str
    variable_type: type[DeviceVariable]


class GenericVariableAttributeIO(AttributeIO[float, GenericVariableAttributeIORef]):
    def __init__(self, device: GenericDevice):
        pass

    async def update(self, attr: AttrR[float, GenericVariableAttributeIORef]):
        pass

    async def send(
        self, attr: AttrW[float, GenericVariableAttributeIORef], value: float
    ):
        pass


class PollingDeviceController(Controller):
    def __init__(self, device: GenericDevice):
        super().__init__(ios=[])
