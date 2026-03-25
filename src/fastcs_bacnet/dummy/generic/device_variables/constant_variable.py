from collections.abc import Callable

from fastcs_bacnet.dummy.generic.device_variables.device_variable import DeviceVariable


class ConstantVariable(DeviceVariable):
    def __init__(
        self,
        name: str,
        value: float,
        update_callback: Callable[[float], None] | None = None,
    ):
        super().__init__(name, update_callback=update_callback)

        self._value = value
