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
    def __init__(
        self,
        device_name: str,
        number_of_constant_fields: int = 0,
        number_of_oscillating_fields: int = 0,
        number_of_random_fields: int = 0,
        number_of_read_write_fields: int = 0,
    ):
        self.variables: list[DeviceVariable] = []

        for i in range(number_of_constant_fields):
            self.variables.append(
                ConstantVariable(f"{device_name}_constant_{i}", random.random())
            )

        for i in range(number_of_oscillating_fields):
            self.variables.append(
                OscillatingVariable(
                    f"{device_name}_oscillating_{i}",
                    random.random(),
                    random.random(),
                    random.random() + 0.5,
                )
            )

        for i in range(number_of_random_fields):
            self.variables.append(
                RandomVariable(
                    f"{device_name}_random_{i}",
                    random.random(),
                    random.random() + 1,
                    random.random(),
                    random.random() + 1,
                )
            )

        for i in range(number_of_read_write_fields):
            self.variables.append(
                ReadWriteVariable(f"{device_name}_oscillating_{i}", random.random())
            )
