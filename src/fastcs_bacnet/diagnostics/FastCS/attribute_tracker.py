from datetime import datetime, timedelta

from fastcs_bacnet.diagnostics.FastCS.tracked_read_attribute import TrackedAttrR


class AttributeTracker:
    recent_times: list[timedelta]
    first_update: datetime | None
    last_update: datetime | None

    def __init__(self, tracked_attribute: TrackedAttrR, history_size: int = 20):

        self.tracked_attribute = tracked_attribute
        self.history_size = history_size

        self.tracked_attribute.set_diagnostic_callback(self.update_callback)

    def update_callback(self, start_time: datetime, end_time: datetime):

        self.recent_times.append(end_time - start_time)
        while len(self.recent_times) > self.history_size:
            self.recent_times.pop(0)

        if self.first_update is None:
            self.first_update = start_time
        self.last_update = start_time
