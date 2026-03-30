from datetime import datetime, timedelta

from bacpypes3.primitivedata import PropertyIdentifier

from fastcs_bacnet.dummy.BAC0.analog_output_object import AnalogOutputObject
from fastcs_bacnet.practical.BAC0.object_subscription import ObjectSubscription


class SubscriptionPair:
    # subscription messages that have been sent but not recieved yet
    sent_buffer: list[tuple[float, datetime]] = []

    # time between sending and recieving updates
    # size limited, only the most recent sent updates are kept
    recent_receival_times: list[timedelta | None] = []

    # max size of recent_recieval_times
    recent_times_buffer_length: int

    total_missed_updates: int = 0
    total_updates_recieved: int = 0
    total_update_wait_time: timedelta

    # when we cant match a recieved value to a sent value
    # shouldnt ever happed but we should definitely know if it does
    total_mystery_updates: int = 0

    def __init__(
        self,
        analog_output_object: AnalogOutputObject,
        object_subscription: ObjectSubscription,
        recent_times_buffer_length: int = 20,
    ):
        self.recent_times_buffer_length = recent_times_buffer_length
        self.total_update_wait_time = timedelta(0)

        # maybe a bit cheeky to acess the analog_ouput_object underlying
        # device variable directly. Should be with a getter??
        analog_output_object.device_variable.set_diagnostic_callback(self._on_send)
        object_subscription.set_diagnostic_callback(self._on_recieve)

    def _on_send(self, new_value: float):
        self.sent_buffer.append((new_value, datetime.now()))

    def _on_recieve(self, property_identifier: str, property_value: float):
        if property_identifier is not PropertyIdentifier.presentValue:
            return

        recieved_time = datetime.now()

        sent_index = self._match(property_value)
        if sent_index is None:
            self.total_mystery_updates += 1
            return

        sent_time = self.sent_buffer[sent_index][1]

        # every sent update before the current one must have been missed
        # remove the sent buffer before the one we recieved
        # add
        for _ in range(sent_index):
            self.sent_buffer.pop(0)
            self.add_recieval_time(None)

        self.sent_buffer.pop(0)
        self.add_recieval_time(recieved_time - sent_time)

    def _match(self, recieved_value: float) -> int | None:

        for i in range(len(self.sent_buffer)):
            sent_value_i = self.sent_buffer[i][0]
            if sent_value_i == recieved_value:
                return i

        return None

    def add_recieval_time(self, receival_time: timedelta | None):

        if receival_time is None:
            self.total_missed_updates += 1
        else:
            self.total_updates_recieved += 1
            self.total_update_wait_time += receival_time

        self.recent_receival_times.append(receival_time)

        while len(self.recent_receival_times) > self.recent_times_buffer_length:
            self.recent_receival_times.pop(0)
