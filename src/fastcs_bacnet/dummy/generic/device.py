import random

from fastcs_bacnet.dummy.generic.device_variables.constant_variable import (
    ConstantVariable,
)
from fastcs_bacnet.dummy.generic.device_variables.device_variable import DeviceVariable
from fastcs_bacnet.dummy.generic.device_variables.oscillating_variable import (
    OscillatingVariable,
)
from fastcs_bacnet.dummy.generic.device_variables.random_variable import RandomVariable
from fastcs_bacnet.dummy.generic.device_variables.read_write_variable import (
    ReadWriteVariable,
)


class Device:
    """
    A generic dummy device for FastCS to interact with
    Stores all its "variables" (equivalent to FastCS attribtues) in one list
    """

    def __init__(
        self,
        device_name: str,
        number_of_constant_fields: int = 0,
        number_of_oscillating_fields: int = 0,
        number_of_random_fields: int = 0,
        number_of_read_write_fields: int = 0,
    ):
        """
        Creates numbers of variables specified by arguments
        Stores them all in one list of device variables
        naming convention is: [device name]_[variable type]_[variable number]
        """
        self._name = device_name
        self._variables: dict[str, DeviceVariable] = {}

        for i in range(number_of_constant_fields):
            name = f"{self._name}_constant_{i}"
            self._variables[name] = ConstantVariable(name, random.random())

        for i in range(number_of_oscillating_fields):
            name = f"{self._name}_oscillating_{i}"
            self._variables[name] = OscillatingVariable(
                name,
                random.random(),
                random.random(),
                random.random() + 0.5,
            )

        for i in range(number_of_random_fields):
            name = f"{self._name}_random_{i}"
            self._variables[name] = RandomVariable(
                name,
                random.random(),
                random.random() + 1,
                random.random(),
                random.random() + 1,
            )

        for i in range(number_of_read_write_fields):
            name = f"{self._name}_oscillating_{i}"
            self._variables[name] = ReadWriteVariable(name, random.random())

    def get_name(self):
        return self._name

    def get_variable_summary(self) -> list[tuple[str, type[DeviceVariable]]]:
        return [(name, type(self._variables[name])) for name in self._variables.keys()]

    def get_variable(self, variable_name) -> DeviceVariable:
        return self._variables[variable_name]

    # there is no method to add variables or it would be
    # too easy to create variables with duplicate names
    # OR share variables between devices
