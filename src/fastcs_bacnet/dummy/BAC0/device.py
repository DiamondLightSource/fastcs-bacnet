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
    def __init__(
        self,
        ip_address: str,
        port: int,
        device_id: int,
        number_of_constant_fields: int = 0,
        number_of_oscillating_fields: int = 0,
        number_of_random_fields: int = 0,
    ):

        self.ip_address = ip_address
        self.port = port
        self.bac0_device = BAC0.start(ip=ip_address, port=port, device_id=device_id)

        self.device_objects: list[AnalogOutputObject] = []

        # Tracks the number of analog outputs that have been made for this object
        # so object ids dont clash
        # TODO: Change this to be a dictionary so it can track all object types
        self.current_analog_output_index: int = 0

        for i in range(number_of_constant_fields):
            self.add_object(ConstantVariable, i)
        for i in range(number_of_oscillating_fields):
            self.add_object(OscillatingVariable, i)
        for i in range(number_of_random_fields):
            self.add_object(RandomVariable, i)

    def add_object(self, variable_class: type[DeviceVariable], index: int):

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
            f"{variable_string} object of device {self.ip_address}:{self.port}"
        )

        if object_variable is not None:
            new_analog_output_object = AnalogOutputObject(
                self.bac0_device,
                object_name,
                object_description,
                self.current_analog_output_index,
                object_variable,
            )
            self.device_objects.append(new_analog_output_object)
            self.current_analog_output_index += 1
