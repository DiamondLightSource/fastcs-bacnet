import asyncio
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
        pass

    def update(self):
        pass
