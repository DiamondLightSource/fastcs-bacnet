import asyncio
import datetime
import math

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
    ):
        super().__init__(device, name, description)

        self.device = device
        self.name = name
        self.amplitude = amplitude
        self.offset = offset
        self.frequency = frequency
        self.refresh_rate = refresh_rate

        asyncio.create_task(self.start_update_loop())

    async def start_update_loop(self):
        self.start_time = datetime.datetime.now()
        while True:
            self.update()
            await asyncio.sleep(self.refresh_rate)

    def update(self, debug=False):
        current_time = datetime.datetime.now()
        dif_time = current_time - self.start_time
        new_dummy_value = self.offset + (
            self.amplitude * math.sin(self.frequency * dif_time.total_seconds())
        )
        if debug:
            print("current value of ", self.name, ": ", new_dummy_value)
        self.device[self.name].presentValue = new_dummy_value
