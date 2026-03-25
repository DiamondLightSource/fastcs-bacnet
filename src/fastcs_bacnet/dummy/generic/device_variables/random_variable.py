import asyncio
import random
from collections.abc import Callable

from fastcs_bacnet.dummy.generic.device_variables.device_variable import DeviceVariable


class RandomVariable(DeviceVariable):
    def __init__(
        self,
        name: str,
        min_change_time: float = 0.0,
        max_change_time: float = 1.0,
        min_value: float = 0.0,
        max_value: float = 1.0,
        update_callback: Callable[[float], None] | None = None,
    ):
        super().__init__(name, update_callback=update_callback)

        self.min_change_time = min_change_time
        self.max_change_time = max_change_time
        self.min_value = min_value
        self.max_value = max_value

        asyncio.create_task(self.start_update_loop())

    async def start_update_loop(self):
        while True:
            self.update()
            change_time = self.min_change_time + (
                random.random() * (self.max_change_time - self.min_change_time)
            )
            await asyncio.sleep(change_time)

    def update(self):
        self._value = self.min_value + (
            random.random() * (self.max_value - self.min_value)
        )

        if self.update_callback is not None:
            self.update_callback(self._value)
