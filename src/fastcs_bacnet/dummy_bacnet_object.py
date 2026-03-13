import asyncio
import datetime
import math
import random

from BAC0.core.devices.local.factory import analog_output


class DummyBACnetObject:
    def __init__(self, device, name, description):

        ref = analog_output(name=name, description=description)
        ref.add_objects_to_application(device)
        ref.clear_objects()


class DummyConstantObject(DummyBACnetObject):
    def __init__(self, device, name, description, value):
        super().__init__(device, name, description)

        device[name].presentValue = value


class DummyOscillatingObject(DummyBACnetObject):
    def __init__(
        self,
        device,
        name,
        description,
        amplitude=1.0,
        offset=0.0,
        frequency=1.0,
        refresh_rate=0.1,
        debug=False,
    ):
        super().__init__(device, name, description)

        self.device = device
        self.name = name
        self.amplitude = amplitude
        self.offset = offset
        self.frequency = frequency
        self.refresh_rate = refresh_rate
        self.debug = debug

        asyncio.create_task(self.start_update_loop())

    async def start_update_loop(self):
        self.start_time = datetime.datetime.now()
        while True:
            self.update()
            await asyncio.sleep(self.refresh_rate)

    def update(self):
        current_time = datetime.datetime.now()
        dif_time = current_time - self.start_time
        new_dummy_value = self.offset + (
            self.amplitude * math.sin(self.frequency * dif_time.total_seconds())
        )
        if self.debug:
            print("current value of ", self.name, ": ", new_dummy_value)
        self.device[self.name].presentValue = new_dummy_value


class DummyRandomChangeObject(DummyBACnetObject):
    def __init__(
        self,
        device,
        name,
        description,
        min_change_time=0.0,
        max_change_time=1.0,
        min_value=0.0,
        max_value=1.0,
        debug=False,
    ):
        super().__init__(device, name, description)

        self.device = device
        self.name = name
        self.min_change_time = min_change_time
        self.max_change_time = max_change_time
        self.min_value = min_value
        self.max_value = max_value
        self.debug = debug

        asyncio.create_task(self.start_update_loop())

    async def start_update_loop(self):
        while True:
            self.update()
            change_time = self.min_change_time + (
                random.random() * (self.max_change_time - self.min_change_time)
            )
            await asyncio.sleep(change_time)

    def update(self):
        new_dummy_value = self.min_value + (
            random.random() * (self.max_value - self.min_value)
        )
        if self.debug:
            print("current value of ", self.name, ": ", new_dummy_value)
        self.device[self.name].presentValue = new_dummy_value
