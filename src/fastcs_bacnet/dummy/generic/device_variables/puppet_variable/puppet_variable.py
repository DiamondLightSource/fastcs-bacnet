from collections.abc import Callable

from fastcs_bacnet.dummy.generic.device_variables.device_variable import (
    DeviceVariable,
)


class PuppetVariable(DeviceVariable):
    """
    A variable thats value is controller by a puppet controller
    The idea is that its lower CPU usage as only one puppet controller is needed
    Looks the same as a ReadWriteVariable but is NOT the same
    Shouldnt be written to from FastCS transport
    """

    def __init__(
        self,
        name: str,
        initial_value: float = 1.0,
        update_callback: Callable[[float, float | None], None] | None = None,
    ):
        super().__init__(name, update_callback=update_callback)
        self._value = initial_value

    def puppet_set_value(self, new_value: float):
        """
        Writes a new value to the variable
        """
        previous_value = self._value
        self._value = new_value

        self.callback_holder.sum_callback(self._value, previous_value)
