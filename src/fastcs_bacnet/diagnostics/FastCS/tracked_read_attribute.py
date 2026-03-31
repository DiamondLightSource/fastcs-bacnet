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
    diagnostic_callback: Callable[[dt, dt], None] | None

    async def update(self, value: Any) -> None:
        update_start_time = dt.now()

        await super().update(value)

        update_end_time = dt.now()

        if self.diagnostic_callback is not None:
            self.diagnostic_callback(update_start_time, update_end_time)

    def set_diagnostic_callback(
        self, diagnostic_callback: Callable[[dt, dt], None] | None
    ):
        self.diagnostic_callback = diagnostic_callback
