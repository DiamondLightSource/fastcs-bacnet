from datetime import datetime


class QueueTracker:
    fastcs_start_time: datetime | None = None
    first_queue_time: datetime | None = None
    first_overflow_time: datetime | None = None
    last_overflow_time: datetime | None = None

    recent_queue_history: list[tuple[int, datetime]]
    history_size: int
    poll_rate: float
    total_lost_requests: int = 0

    def __init__(
        self, fastcs_coroutine=None, poll_rate: float = 1.0, history_size: int = 20
    ):
        self.fastcs_coroutine = fastcs_coroutine
        self.poll_rate = poll_rate
        self.history_size = history_size

    def start(self):
        pass

    def poll(self):
        pass

    def set_fastcs_start_time(self, fast_cs_start_time: datetime):
        pass
