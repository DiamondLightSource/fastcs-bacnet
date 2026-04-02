import random

from fastcs_bacnet.dummy.generic.device_variables.puppet_variable.puppet_variable import (  # noqa: E501
    PuppetVariable,
)
from fastcs_bacnet.dummy.generic.device_variables.random_variable import RandomVariable


class PuppetController:
    variables: list[PuppetVariable]

    def __init__(self, initial_variables: list[PuppetVariable], update_loops: int = 1):

        self.variables = []

        for puppet_variable in initial_variables:
            self.add_puppet_variable(puppet_variable)

    def add_puppet_variable(self, puppet_variable: PuppetVariable):
        self.variables.append(puppet_variable)

    def _start_update_loops(self, update_loops: int):

        for i in range(update_loops):
            RandomVariable(
                "puppet_random_" + str(i), update_callback=self._update_random_variable
            )

    def _update_random_variable(self, new_value: float):

        variable_index: int = int(len(self.variables) * random.random())

        self.variables[variable_index].puppet_set_value(new_value)
