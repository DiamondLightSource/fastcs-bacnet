from datetime import datetime, timedelta

from fastcs_bacnet.dummy.BAC0.analog_output_object import AnalogOutputObject
from fastcs_bacnet.practical.BAC0.object_subscription import ObjectSubscription


class SubscriptionPair:
    # subscription messages that have been sent but not recieved yet
    sent_buffer: list[tuple[float, datetime]] = []

    # time between sending and recieving updates
    # size limited, only the most recent sent updates are kept
    recent_receival_times: list[timedelta] = []

    # max size of recent_recieval_times
    recent_times_buffer_length: int

    total_missed_updates: int = 0
    total_updates_recieved: int = 0
    total_update_wait_time: timedelta

    def __init__(
        self,
        analog_output_object: AnalogOutputObject,
        object_subscription: ObjectSubscription,
    ):
        pass

    def _on_send(self, new_value: float):
        pass

    def _on_recieve(self, property_identifier: str, property_value: float):
        pass
