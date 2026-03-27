import BAC0
from BAC0.core.devices.local.factory import analog_output

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

        device_variable.set_update_callback(self._update_value)

    def _update_value(self, new_value: float):
        """
        Callback function to update this objects value
        """
        # Ruff doesnt like this
        # It is the way they do it in the docs
        # Sometime Ruff is fine with it??
        self.device[self.name].presentValue = new_value  # type: ignore
