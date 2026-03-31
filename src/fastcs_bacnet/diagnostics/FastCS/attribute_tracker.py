from datetime import datetime, timedelta

from fastcs_bacnet.diagnostics.FastCS.tracked_read_attribute import TrackedAttrR


class AttributeTracker:
    """
    Records and stores updates times from a TrackedAttrR
    """

    _recent_times: list[timedelta]
    _first_update: datetime | None
    _last_update: datetime | None

    def __init__(self, tracked_attribute: TrackedAttrR, history_size: int = 20):
        """
        tracked_attribute: Attribute to track
        history_size: Maximum number of update times to store in the recent_times queue
        """

        self._tracked_attribute = tracked_attribute
        self._history_size = history_size

        self._tracked_attribute.set_diagnostic_callback(self.update_callback)

    def update_callback(self, start_time: datetime, end_time: datetime):
        """
        The callback function that gets called after the attributes
        update method is called
        start_time is when the update method is first called
        end_time is after the original update method has been resolved
        """

        self._recent_times.append(end_time - start_time)
        while len(self._recent_times) > self._history_size:
            self._recent_times.pop(0)

        if self._first_update is None:
            self._first_update = start_time
        self._last_update = start_time
