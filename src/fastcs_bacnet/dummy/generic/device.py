from fastcs_bacnet.dummy.generic.device_variables.device_variable import DeviceVariable


class Device:
    def __init__(
        self,
        device_name: str,
        number_of_constant_fields: int = 0,
        number_of_oscillating_fields: int = 0,
        number_of_random_fields: int = 0,
        number_of_read_write_fields: int = 0,
    ):
        self.variables: list[DeviceVariable] = []

        pass
