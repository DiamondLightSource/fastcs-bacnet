import BAC0

from fastcs_bacnet.dummy.BAC0.analog_output_object import AnalogOutputObject


class Device:
    def __init__(
        self,
        ip_address: str,
        port: int,
        device_id: int,
        number_of_constant_fields: int = 0,
        number_of_oscillating_fields: int = 0,
        number_of_random_fields: int = 0,
    ):

        bac0_device = BAC0.start(ip=ip_address, port=port, device_id=device_id)  # noqa: F841

        device_objects: list[AnalogOutputObject] = []  # noqa: F841

        # Tracks the number of analog outputs that have been made for this object
        # so object ids dont clash
        # TODO: Change this to be a dictionary so it can track all object types
        current_analog_output_index: int = 0  # noqa: F841

        # TODO: Create objects here
