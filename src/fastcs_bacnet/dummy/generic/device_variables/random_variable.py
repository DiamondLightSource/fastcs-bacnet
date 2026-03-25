import asyncio
import random
from collections.abc import Callable

from fastcs_bacnet.dummy.generic.device_variables.device_variable import DeviceVariable


class RandomVariable(DeviceVariable):
    """
    Device variable that changes to a random value after random time periods
    Callback is called when value changes
    """

    def __init__(
        self,
        name: str,
        min_change_time: float = 0.0,
        max_change_time: float = 1.0,
        min_value: float = 0.0,
        max_value: float = 1.0,
        update_callback: Callable[[float], None] | None = None,
    ):
        """
        min_change_time: Minimum time between variable changes
        max_change_time: Maximum time between variable changes
        min_value: Minimum value the variable could be
        max_value: Maximum value the variable could be

        update loop is started automatically after initialisation
        """
        super().__init__(name, update_callback=update_callback)

        self.min_change_time = min_change_time
        self.max_change_time = max_change_time
        self.min_value = min_value
        self.max_value = max_value

        asyncio.create_task(self.start_update_loop())

    async def start_update_loop(self):
        """
        The loop that updates the variable's value after random intervals
        After each update a random time is decided
            (uniform distribution between min and max time)
        The loop waits for that time period and updates again
        """
        while True:
            self.update()
            change_time = self.min_change_time + (
                random.random() * (self.max_change_time - self.min_change_time)
            )
            await asyncio.sleep(change_time)

    def update(self):
        """
        Randomly assigns a new value to the variable
            (uniform distribution between min and max value)
        """
        self._value = self.min_value + (
            random.random() * (self.max_value - self.min_value)
        )

        if self.update_callback is not None:
            self.update_callback(self._value)
