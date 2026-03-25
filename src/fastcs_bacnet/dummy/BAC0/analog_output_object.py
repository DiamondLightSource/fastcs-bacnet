import BAC0
from BAC0.core.devices.local.factory import analog_output

from fastcs_bacnet.dummy.generic.device_variables.device_variable import DeviceVariable


class AnalogOutputObject:
    def __init__(
        self,
        device: BAC0.lite,
        name: str,
        description: str,
        instance: int,
        device_variable: DeviceVariable,
    ):
        self.device = device
        self.name = name
        self.device_variable = device_variable

        ref = analog_output(name=name, description=description, instance=instance)
        ref.add_objects_to_application(device)
        ref.clear_objects()

        device_variable.set_update_callback(self._update_value)

    def _update_value(self, new_value: float):
        self.device[self.name].presentValue = new_value  # type: ignore
