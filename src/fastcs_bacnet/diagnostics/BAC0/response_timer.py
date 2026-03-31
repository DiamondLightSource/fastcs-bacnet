from fastcs_bacnet.diagnostics.BAC0.subscription_pair import SubscriptionPair
from fastcs_bacnet.dummy.BAC0.analog_output_object import AnalogOutputObject
from fastcs_bacnet.practical.BAC0.object_subscription import ObjectSubscription


class ResponseTimer:
    """
    Class for managing a list of SubscriptionPair s
    """

    # May want to change to a dictionary??
    # Most of the operations invlolve iterating through it
    # But getting a specific value using keys is also used
    _subscription_pairs: list[SubscriptionPair] = []

    def __init__(self, recent_times_buffer_length: int = 20):
        self._recent_times_buffer_length = recent_times_buffer_length

    def add_subscription_pair(
        self,
        analog_output_object: AnalogOutputObject,
        object_subscription: ObjectSubscription,
    ):
        """
        Creates a subscription pair from the input objects and adds it to the list
        """
        self._subscription_pairs.append(
            SubscriptionPair(
                analog_output_object,
                object_subscription,
                recent_times_buffer_length=self._recent_times_buffer_length,
            )
        )

    def remove_subscription_pair(self, index: int):
        """
        Removes a subscription pair from the list at a specific index
        Stops the subscription
        Find index of a pair using index_from methods
        """
        subscription_pair = self._subscription_pairs.pop(index)
        subscription_pair.stop_recording()

    def index_from_device_object(
        self, analog_output_object: AnalogOutputObject
    ) -> int | None:
        """
        Gets index of a subscription pair from its analog_output_object
        """
        for index in range(len(self._subscription_pairs)):
            index_analog_output_object = self._subscription_pairs[
                index
            ].get_analog_output_object()
            if analog_output_object == index_analog_output_object:
                return index
        return None

    def index_from_object_subscription(
        self, object_subscription: ObjectSubscription
    ) -> int | None:
        """
        Gets index of a subscription pair from its object_subscription
        """
        for index in range(len(self._subscription_pairs)):
            index_object_subscription = self._subscription_pairs[
                index
            ].get_object_subscription()
            if object_subscription == index_object_subscription:
                return index
        return None
