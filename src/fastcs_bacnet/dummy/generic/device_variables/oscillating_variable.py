import asyncio
import math
from collections.abc import Callable
from datetime import datetime as dt

from fastcs_bacnet.dummy.generic.device_variables.device_variable import (
    DeviceVariable,
    DVCallbackParameters,
)


class OscillatingVariable(DeviceVariable):
    """
    A device variable whose value oscillates over time (sinosodial pattern)
    Since the value is technically always changing it is only updated periodically
    Callback is called on value updates
    """

    def __init__(
        self,
        name: str,
        amplitude: float = 1.0,
        offset: float = 0.0,
        frequency: float = 1.0,
        value_refresh_period: float = 1.2,
        update_callback: Callable[[*DVCallbackParameters], None] | None = None,
    ):
        """
        amplitude: Amplitude of the sin wave
            (half of hte difference between its maximum and minimum)
        offset: The y difference between the centre of the waves oscillation
            and the y axis
        frequency: The number of oscillations per second
        value_refresh_period: The time between updating the variables value

        update loop is started automatically after initialisation
        """
        super().__init__(name, update_callback=update_callback)

        self.amplitude = amplitude
        self.offset = offset
        self.frequency = frequency
        self.value_refresh_period = value_refresh_period

        asyncio.create_task(self._start_update_loop())

    async def _start_update_loop(self):
        """
        The loop that periodically updates the variable's value
        Records start time and calls update() every value_refresh_period seconds
        """
        self.start_time = dt.now()
        while True:
            self._update()
            await asyncio.sleep(self.value_refresh_period)

    def _update(self):
        """
        Updates the variable's value based on the current time and wave attributes
        Value = offset + (amplitude * sin(frequency * t * 2PI))
        Where t is time since update loop started
        """
        current_time = dt.now()
        dif_time = current_time - self.start_time

        previous_value = self._value

        self._value = self.offset + (
            self.amplitude
            * math.sin(self.frequency * dif_time.total_seconds() * math.pi * 2)
        )

        self.callback_stack.sum_callback(self._value, previous_value)  # type: ignore
