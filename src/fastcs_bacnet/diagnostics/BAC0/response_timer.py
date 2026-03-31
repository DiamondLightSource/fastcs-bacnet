from fastcs_bacnet.diagnostics.BAC0.subscription_pair import SubscriptionPair
from fastcs_bacnet.dummy.BAC0.analog_output_object import AnalogOutputObject
from fastcs_bacnet.practical.BAC0.object_subscription import ObjectSubscription


class ResponseTimer:
    subscription_pairs: list[SubscriptionPair] = []

    def __init__(self, recent_times_buffer_length: int = 20):
        self._recent_times_buffer_length = recent_times_buffer_length

    def add_subscription_pair(
        self,
        analog_output_object: AnalogOutputObject,
        object_subscription: ObjectSubscription,
    ):
        self.subscription_pairs.append(
            SubscriptionPair(
                analog_output_object,
                object_subscription,
                recent_times_buffer_length=self._recent_times_buffer_length,
            )
        )
