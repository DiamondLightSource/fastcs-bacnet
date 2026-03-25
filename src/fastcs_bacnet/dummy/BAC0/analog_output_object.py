import BAC0
from BAC0.core.devices.local.factory import analog_output


class AnalogOutputObject:
    def __init__(
        self,
        device: BAC0.start,
        name: str,
        description: str,
        instance: int,
    ):
        ref = analog_output(name=name, description=description, instance=instance)
        ref.add_objects_to_application(device)
        ref.clear_objects()
