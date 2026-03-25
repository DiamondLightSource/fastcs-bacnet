import asyncio
import math
from collections.abc import Callable
from datetime import datetime as dt

from fastcs_bacnet.dummy.generic.device_variables.device_variable import DeviceVariable


class OscillatingVariable(DeviceVariable):
    def __init__(
        self,
        name: str,
        amplitude: float = 1.0,
        offset: float = 0.0,
        frequency: float = 1.0,
        value_refresh_period: float = 0.2,
        update_callback: Callable[[float], None] | None = None,
    ):
        super().__init__(name, update_callback=update_callback)

        self.amplitude = amplitude
        self.offset = offset
        self.frequency = frequency
        self.value_refresh_period = value_refresh_period

        asyncio.create_task(self.start_update_loop())

    async def start_update_loop(self):
        self.start_time = dt.now()
        while True:
            self.update()
            await asyncio.sleep(self.value_refresh_period)

    def update(self):
        current_time = dt.now()
        dif_time = current_time - self.start_time

        self._value = self.offset + (
            self.amplitude * math.sin(self.frequency * dif_time.total_seconds())
        )

        if self.update_callback is not None:
            self.update_callback(self._value)
