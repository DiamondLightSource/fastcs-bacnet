from abc import ABC
from collections.abc import Callable

from fastcs_bacnet.practical.generic.callback_stack import CallbackStack


class DeviceVariable(ABC):
    """
    Abstract class for a variable belonging to a device
    This is intended to represent any of
        A bacnet device Object
        An EPICS PV
        A FastCS Attribute
    """

    _value: float | None
    callback_stack: CallbackStack[float | None, float]

    def __init__(
        self,
        name: str,
        update_callback: Callable[[float | None, float], None] | None = None,
    ):
        """
        name: name of variable, should be unique per device
        update_callback: procedure that runs when variable value is updated
        """
        self._value = None
        self.name = name

        self.callback_stack = CallbackStack[float | None, float]()
        if update_callback is not None:
            self.callback_stack.add_to_stack(update_callback)

    def get_value(self) -> float | None:
        """
        Returns value of variable
        """
        return self._value
