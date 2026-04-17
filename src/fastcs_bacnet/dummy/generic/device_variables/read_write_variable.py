from collections.abc import Callable

from fastcs_bacnet.dummy.generic.device_variables.device_variable import (
    DeviceVariable,
    DVCallbackParameters,
)


class ReadWriteVariable(DeviceVariable):
    """
    Writable device variable
    Callback is called when value is written
        (even if the new value is the same)
    """

    def __init__(
        self,
        name: str,
        initial_value: float = 0.0,
        update_callback: Callable[[*DVCallbackParameters], None] | None = None,
    ):
        super().__init__(name, update_callback=update_callback)

        self._value = initial_value

    def set_value(self, value: float):
        """
        Writes a new value to the variable
        """
        previous_value = self._value
        self._value = value

        self.callback_stack.sum_callback(self._value, previous_value)  # type: ignore
