from collections.abc import Callable
from datetime import datetime as dt
from typing import Any

from fastcs.attributes.attr_r import AttrR
from fastcs.attributes.attribute_io_ref import AttributeIORefT
from fastcs.datatypes import DType_T


# this could maybe be done with add_on_update_callback AttrR method??
# Might also just not take any time at all??
# Does fastcs update transports using the update callbacks??
# In that case we couldnt add our own callback
# as were measuring the time it takes to call the callbacks
class TrackedAttrR(AttrR[DType_T, AttributeIORefT]):
    """
    Extension of the fastcs AttrR class
    Overrides the update method to record start and finish times
    Calls a callback with the times after
    """

    _diagnostic_callback: Callable[[dt, dt], None] | None

    async def update(self, value: Any) -> None:
        """
        Overridden update method
        Records start time
        Waits for the original update method to call
        Records end time
        Then calls callback with the times as arguments
        """
        update_start_time = dt.now()

        await super().update(value)

        update_end_time = dt.now()

        if self._diagnostic_callback is not None:
            self._diagnostic_callback(update_start_time, update_end_time)

    def set_diagnostic_callback(
        self, diagnostic_callback: Callable[[dt, dt], None] | None
    ):
        self._diagnostic_callback = diagnostic_callback
