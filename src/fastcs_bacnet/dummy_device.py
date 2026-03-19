# a lot of repeated code from dummy_bacnet_object.py
# maybe its worth cleaning this up??
import datetime
import enum
import math
import random


# could probably use class types instead but I am not good enough for that :(
class FieldType(enum.Enum):
    CONSTANT = 0
    OSCILLATING = 1
    RANDOM = 2
    WRITABLE = 3


class DummyDevice:
    def __init__(
        self,
        number_of_constant_fields=0,
        number_of_oscillating_fields=0,
        number_of_random_fields=0,
        number_of_read_write_fields=0,
    ):
        self.constant_fields: list[ConstantField] = []
        self.oscillating_fields: list[OscillatingField] = []
        self.random_fields: list[RandomField] = []
        self.rw_fields: list[ReadWriteField] = []

        for _ in range(number_of_constant_fields):
            self.constant_fields.append(ConstantField(random.random()))

        for _ in range(number_of_oscillating_fields):
            self.oscillating_fields.append(
                OscillatingField(
                    random.random(), random.random(), random.random() + 0.5
                )
            )

        for _ in range(number_of_random_fields):
            self.random_fields.append(
                RandomField(
                    random.random(),
                    random.random() + 1,
                    random.random(),
                    random.random() + 1,
                )
            )

        for _ in range(number_of_read_write_fields):
            self.rw_fields.append(ReadWriteField(random.random()))

    def get_value(self, field_type, index) -> float:

        if field_type == FieldType.CONSTANT:
            return self.constant_fields[index].get_value()

        if field_type == FieldType.OSCILLATING:
            return self.oscillating_fields[index].get_value()

        if field_type == FieldType.RANDOM:
            return self.random_fields[index].get_value()

        if field_type == FieldType.WRITABLE:
            return self.rw_fields[index].get_value()

        return 0.0


class Field:
    def __init__(self):
        pass

    def get_value(self) -> float:
        return 0.0


class ConstantField(Field):
    def __init__(self, value: float):
        self.value = value

    def get_value(self):
        return self.value


class OscillatingField(Field):
    def __init__(
        self, amplitude: float = 1.0, offset: float = 0.0, frequency: float = 1.0
    ):
        self.amplitude = amplitude
        self.offset = offset
        self.frequency = frequency
        self.start_time = datetime.datetime.now()

    def get_value(self):
        current_time = datetime.datetime.now()
        dif_time = current_time - self.start_time
        current_value = self.offset + (
            self.amplitude * math.sin(self.frequency * dif_time.total_seconds())
        )

        return current_value


class RandomField(Field):
    def __init__(
        self,
        min_change_time=0.0,
        max_change_time=1.0,
        min_value=0.0,
        max_value=1.0,
    ):
        self.min_change_time = min_change_time
        self.max_change_time = max_change_time
        self.min_value = min_value
        self.max_value = max_value
        self.generate_new_value()

    def generate_new_value(self):
        self.value = self.min_value + (
            random.random() * (self.max_value - self.min_value)
        )
        self.last_update = datetime.datetime.now()
        self.next_update_in = self.min_change_time + (
            random.random() * (self.max_change_time - self.min_change_time)
        )

    def get_value(self):
        # kind of hacky
        # supposed to update value in random time intervals
        # instead it sets a time interval to update in
        # next time the value is checked it checks if it should have updated
        # if so, it updates and sets a new time
        time_since_last_update = datetime.datetime.now() - self.last_update
        if time_since_last_update.total_seconds() > self.next_update_in:
            self.generate_new_value()

        return self.value


class ReadWriteField(Field):
    def __init__(self, initial_value=0.0):
        self.value = initial_value

    def get_value(self):
        return self.value

    def set_value(self, new_value):
        self.value = new_value
