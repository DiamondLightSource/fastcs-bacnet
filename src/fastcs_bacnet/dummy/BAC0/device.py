import random

import BAC0

from fastcs_bacnet.dummy.BAC0.analog_output_object import AnalogOutputObject
from fastcs_bacnet.dummy.generic.device_variables.constant_variable import (
    ConstantVariable,
)
from fastcs_bacnet.dummy.generic.device_variables.device_variable import DeviceVariable
from fastcs_bacnet.dummy.generic.device_variables.oscillating_variable import (
    OscillatingVariable,
)
from fastcs_bacnet.dummy.generic.device_variables.random_variable import RandomVariable


class Device:
    """
    A dummy bacnet device a bacnet client can talk to
    """

    def __init__(
        self,
        ip_address: str,
        port: int,
        device_id: int,
        number_of_constant_fields: int = 0,
        number_of_oscillating_fields: int = 0,
        number_of_random_fields: int = 0,
    ):
        """
        Creates a new bacnet device instance (BAC0.lite)
        And adds objects to it according to parameters
        """

        self._ip_address = ip_address
        self._port = port
        self._bac0_device = BAC0.start(ip=ip_address, port=port, device_id=device_id)

        self._device_objects: dict[str, AnalogOutputObject] = {}

        # Tracks the number of analog outputs that have been made for this object
        # so object ids dont clash
        # TODO: Change this to be a dictionary so it can track all object types
        self._current_analog_output_index: int = 0

        for i in range(number_of_constant_fields):
            self.add_object(ConstantVariable, i)
        for i in range(number_of_oscillating_fields):
            self.add_object(OscillatingVariable, i)
        for i in range(number_of_random_fields):
            self.add_object(RandomVariable, i)

    def add_object(self, variable_class: type[DeviceVariable], index: int):
        """
        variable_class: type of a device variable
            intentionally not an instance
            otherwise one variable could belong to 2 devices
        index: index of the variable type on this object
            doesnt have to be consecutive, just for naming purposes
        Adds an object of a given type to the bacnet device
        """

        variable_string: str = ""
        object_variable: DeviceVariable | None = None

        # TODO: change to a switch statement
        # this could also potentially be automated in other ways
        if variable_class == ConstantVariable:
            variable_string = "constant"
            object_variable = ConstantVariable(variable_string, random.random())
        elif variable_class == OscillatingVariable:
            variable_string = "oscillating"
            object_variable = OscillatingVariable(variable_string)
        elif variable_class == RandomVariable:
            variable_string = "random"
            object_variable = RandomVariable(variable_string)
        object_name = f"{variable_string}_object_{index}"
        object_description = (
            f"{variable_string} object of device {self._ip_address}:{self._port}"
        )

        if object_variable is not None:
            new_analog_output_object = AnalogOutputObject(
                self._bac0_device,
                object_name,
                object_description,
                self._current_analog_output_index,
                object_variable,
            )
            self._device_objects[object_name] = new_analog_output_object
            self._current_analog_output_index += 1

    def object_identifier_from_name(self, object_name: str) -> tuple[str, int]:
        """
        Gets identifying information (type of object and instance) from an object name
        """
        # this will need to change as more object types are used
        return ("analog-output", self._device_objects[object_name].instance)

    # TODO: add methods to get necessary class properties
    # remember to copy lists and thier objects so they cant be manipulated
