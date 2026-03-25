from abc import ABC
from collections.abc import Callable


class DeviceVariable(ABC):
    """
    Abstract class for a variable belonging to a device
    This is intended to represent any of
        A bacnet device Object
        An EPICS PV
        A FastCS Attribute
    """

    _value: float | None

    def __init__(
        self, name: str, update_callback: Callable[[float], None] | None = None
    ):
        """
        name: name of variable, should be unique per device
        update_callback: procedure that runs when variable value is updated
        """
        self.name = name
        self.update_callback = update_callback

    def get_value(self) -> float | None:
        """
        Returns value of variable
        """
        return self._value

    def set_update_callback(self, update_callback: Callable[[float], None] | None):
        """
        Changes the callback procedure of this variable
        Use argument None to remove the current callback
        This will affect updates immediately after the method is called
        """
        self.update_callback = update_callback
