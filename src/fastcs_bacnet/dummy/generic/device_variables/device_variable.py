from abc import ABC
from collections.abc import Callable

from fastcs_bacnet.dummy.generic.device_variables.callback_holder import CallbackHolder


class DeviceVariable(ABC):
    """
    Abstract class for a variable belonging to a device
    This is intended to represent any of
        A bacnet device Object
        An EPICS PV
        A FastCS Attribute
    """

    _value: float | None
    # you will see a lot of type ignores where I unpack DVCallbackParameters into
    # CallbackStack or related methods. This is because pylance struggles with
    # unpacking a tuple of type parameters into ParamSpec (I think)
    # Unpacking (the *) is the same as writing the contents of the tuple out without
    # the surrounding data structure.
    # e.g.: *tuple[float, float | None] == float, float | None
    # Pylance is fine if I write it the long way, therefore I can only assume it is the
    # the one who is wrong
    callback_stack: CallbackHolder

    def __init__(
        self,
        name: str,
        update_callback: Callable[[float, float | None], None] | None = None,
    ):
        """
        name: name of variable, should be unique per device
        update_callback: procedure that runs when variable value is updated
        """
        self._value = None
        self.name = name

        self.callback_stack = CallbackHolder()
        if update_callback is not None:
            self.callback_stack.add(update_callback)

    def get_value(self) -> float | None:
        """
        Returns value of variable
        """
        return self._value
