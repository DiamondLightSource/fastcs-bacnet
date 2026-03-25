from collections.abc import Callable

from fastcs_bacnet.dummy.generic.device_variables.device_variable import DeviceVariable


class ReadWriteVariable(DeviceVariable):
    def __init__(
        self,
        name: str,
        initial_value: float = 0.0,
        update_callback: Callable[[float], None] | None = None,
    ):
        super().__init__(name, update_callback=update_callback)

        self._value = initial_value

    def set_value(self, value: float):
        self._value = value

        if self.update_callback is not None:
            self.update_callback(self._value)
