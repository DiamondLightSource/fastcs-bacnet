import random

from fastcs_bacnet.dummy.generic.device_variables.puppet_variable.puppet_variable import (  # noqa: E501
    PuppetVariable,
)
from fastcs_bacnet.dummy.generic.device_variables.random_variable import RandomVariable


class PuppetController:
    """
    Class to control puppet variables
    Currently uses a RandomVariable to upadte one puppet at a time randomly
    """

    variables: list[PuppetVariable]

    def __init__(
        self, initial_variables: list[PuppetVariable], update_loops: int = 1, **kwargs
    ):
        """
        Adds all initial PuppetVariables
        Does NOT start the update loop
        initial_variables: Variables to be controller by this controller
            PuppetVariables should only be controlled by one controller
        update_loops: The number of RandomVariables to start
        **kwargs: keyword arguments for the RandomVariables
        """

        self.variables = []
        self.update_loops_started = False

        for puppet_variable in initial_variables:
            self.add_puppet_variable(puppet_variable)

    def add_puppet_variable(self, puppet_variable: PuppetVariable):
        self.variables.append(puppet_variable)

    def start_update_loops(self, update_loops: int, **kwargs):
        """
        Creates update_loops s RandomVariables
        Sets the callback to _update_random_variable
        keyword arguments are sent straight to the RandomVariable constructor
        """
        if self.update_loops_started:
            return
        self.update_loops_started = True

        for i in range(update_loops):
            RandomVariable(
                "puppet_random_" + str(i),
                update_callback=self._update_random_variable,
                **kwargs,
            )

    def _update_random_variable(self, new_value: float):
        """
        Gives a random PuppetVariable in the list new_value
        """

        variable_index: int = int(len(self.variables) * random.random())

        self.variables[variable_index].puppet_set_value(new_value)
