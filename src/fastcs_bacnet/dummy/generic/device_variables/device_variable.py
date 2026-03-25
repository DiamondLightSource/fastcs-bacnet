from abc import ABC
from collections.abc import Callable


class DeviceVariable(ABC):
    _value: float | None

    def __init__(
        self, name: str, update_callback: Callable[[float], None] | None = None
    ):
        self.name = name
        self.update_callback = update_callback

    def get_value(self) -> float | None:
        return self._value

    def set_update_callback(self, update_callback: Callable[[float], None] | None):
        self.update_callback = update_callback
