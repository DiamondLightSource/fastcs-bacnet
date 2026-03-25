import asyncio
from collections.abc import Callable

from fastcs_bacnet.dummy.generic.device_variables.device_variable import DeviceVariable


class OscillatingVariable(DeviceVariable):
    def __init__(
        self,
        name: str,
        amplitude: float = 1.0,
        offset: float = 0.0,
        frequency: float = 1.0,
        value_refresh_rate: float = 0.2,
        update_callback: Callable[[float], None] | None = None,
    ):
        super().__init__(name, update_callback=update_callback)

        self.amplitude = amplitude
        self.offset = offset
        self.frequency = frequency
        self.value_refresh_rate = value_refresh_rate

        asyncio.create_task(self.start_update_loop())

    async def start_update_loop(self):
        pass

    def update(self):
        pass
