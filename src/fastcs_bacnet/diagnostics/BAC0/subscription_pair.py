import math
from datetime import datetime, timedelta

from bacpypes3.primitivedata import PropertyIdentifier

from fastcs_bacnet.dummy.BAC0.analog_output_object import AnalogOutputObject
from fastcs_bacnet.practical.BAC0.object_subscription import ObjectSubscription


class SubscriptionPair:
    """
    A class to track the time between an AnalogOutputObject being updated and its
    corresponding ObjectSubscription recieving the update and related statistics
    """

    # subscription messages that have been sent but not recieved yet
    _sent_buffer: list[tuple[float, datetime]] = []

    # time between sending and recieving updates
    # size limited, only the most recent sent updates are kept
    _recent_receival_times: list[timedelta | None] = []

    # max size of recent_recieval_times
    _recent_times_buffer_length: int

    _total_missed_updates: int = 0
    _total_updates_recieved: int = 0
    _total_update_wait_time: timedelta

    # when we cant match a recieved value to a sent value
    # shouldnt ever happed but we should definitely know if it does
    _total_mystery_updates: int = 0

    def __init__(
        self,
        analog_output_object: AnalogOutputObject,
        object_subscription: ObjectSubscription,
        recent_times_buffer_length: int = 20,
    ):
        """
        analog_output_object: analog object of a dummy bacnet device
            (cannot replicate this for real devices)
        object_subscription: subscription object of a bacnet client device that
            subscribes to the analog output object
        recent_times_buffer_length: The number of send-recieve time differences to hold
            at once. List would quickly get very large if this was not capped
        Changes the diagnostic callback function of both objects to _on_send
        and _on_recieve respectively
        """
        self._recent_times_buffer_length = recent_times_buffer_length
        self._total_update_wait_time = timedelta(0)
        self._analog_output_object = analog_output_object
        self._object_subscription = object_subscription

        # maybe a bit cheeky to acess the analog_ouput_object underlying
        # device variable directly. Should be with a getter??
        self._analog_output_object.device_variable.set_diagnostic_callback(
            self._on_send
        )
        self._object_subscription.set_diagnostic_callback(self._on_recieve)

    def _on_send(self, new_value: float):
        """
        Callback to run when an update is sent by the device output object
        Adds the update value and the current time to the _sent_buffer list
        """
        self._sent_buffer.append((new_value, datetime.now()))

    def _on_recieve(self, property_identifier: str, property_value: float):
        """
        Callback to run when an update is recieved by the subscription object
        Matches the recieved value to one that was sent by the device object
        Values sent before the matched send value are marked as missed
        Records the time between the update being sent and recieved
        Adds recorded time as well as missed values to the _recent_recieval_times
        """
        if property_identifier != PropertyIdentifier.presentValue:
            return

        recieved_time = datetime.now()

        sent_index = self._match(property_value)
        if sent_index is None:
            self._total_mystery_updates += 1
            return

        sent_time = self._sent_buffer[sent_index][1]

        # every sent update before the current one must have been missed
        # remove the sent buffer before the one we recieved
        # add
        for _ in range(sent_index):
            self._sent_buffer.pop(0)
            self._add_recieval_time(None)

        self._sent_buffer.pop(0)
        self._add_recieval_time(recieved_time - sent_time)

    def _match(self, recieved_value: float) -> int | None:
        """
        Matches a recieved update value to the most recent matching value from the
        sent updates list
        Returns the index of the matching value
        """

        for i in range(len(self._sent_buffer)):
            sent_value_i = self._sent_buffer[i][0]
            if math.isclose(sent_value_i, recieved_value, rel_tol=0.0001):
                return i

        return None

    def _add_recieval_time(self, receival_time: timedelta | None):
        """
        Adds a time difference (between sending and recieving)
        to the _recent_receival_times list
        Also handles changing of total missed updates, recieved updates and wait time
        As well as keepin gthe list below its maximum length
        """

        if receival_time is None:
            self._total_missed_updates += 1
        else:
            self._total_updates_recieved += 1
            self._total_update_wait_time += receival_time

        self._recent_receival_times.append(receival_time)

        while len(self._recent_receival_times) > self._recent_times_buffer_length:
            self._recent_receival_times.pop(0)

    def get_recent_recieval_times(self) -> list[timedelta | None]:
        """
        Returns a copy of recent_recieval_times
        Dont have to deep copy as timedeltas are immutable
        """
        return list(self._recent_receival_times)

    def get_total_missed_updates(self) -> int:
        return self._total_missed_updates + len(self._sent_buffer)

    def get_average_update_time(self) -> timedelta:
        return self._total_update_wait_time / self._total_updates_recieved

    def get_analog_output_object(self) -> AnalogOutputObject:
        return self._analog_output_object

    def get_object_subscription(self) -> ObjectSubscription:
        return self._object_subscription

    def stop_recording(self):
        self._analog_output_object.device_variable.set_diagnostic_callback(None)
        self._object_subscription.set_diagnostic_callback(None)
