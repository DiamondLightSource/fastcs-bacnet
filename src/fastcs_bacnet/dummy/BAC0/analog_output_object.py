from BAC0.core.devices.local.factory import analog_output

import BAC0
from fastcs_bacnet.dummy.generic.device_variables.device_variable import DeviceVariable


class AnalogOutputObject:
    """
    Simulates a bacnet device object
    Takes a DeviceVariable and mimics its values
    """

    def __init__(
        self,
        device: BAC0.lite,
        name: str,
        description: str,
        instance: int,
        device_variable: DeviceVariable,
    ):
        """
        device: The device the object is being attached to
        name: name of the object
        description: description of the object
        instance: instance number of this object on this device
        device_variable: the DeviceVariable this object will mimic

        Instance numbers must be unique per object type per device
        This is the devices responsibility to handle

        The device_variable's callback will be replaced
        This is how the object mimics its value
        """

        self.device = device
        self.name = name
        self.device_variable = device_variable
        self.instance = instance

        ref = analog_output(name=name, description=description, instance=self.instance)
        ref.add_objects_to_application(device)
        ref.clear_objects()

        initial_value = device_variable.get_value()
        if initial_value is not None:
            self._update_value(initial_value, None)

        device_variable.callback_holder.add(self._update_value)

    def _update_value(self, new_value: float, previous_value: float | None):
        """
        Callback function to update this objects value
        """
        # bad typing from BAC0 library, have to ignore this ruff error
        self.device[self.name].presentValue = new_value  # type: ignore
