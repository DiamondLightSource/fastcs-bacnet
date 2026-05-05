from collections.abc import Callable

from fastcs_bacnet.dummy.generic.device_variables.device_variable import (
    DeviceVariable,
    DVCallbackParameters,
)


class ConstantVariable(DeviceVariable):
    """
    A constant device variable
    Value is set on initialisation and cannot change
    Can be queried
    update callback is included for consistency but does nothing
    """

    def __init__(
        self,
        name: str,
        value: float,
        update_callback: Callable[[*DVCallbackParameters], None] | None = None,
    ):
        super().__init__(name, update_callback=update_callback)

        self._value = value
