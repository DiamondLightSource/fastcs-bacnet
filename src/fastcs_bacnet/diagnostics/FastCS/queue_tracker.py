import asyncio
from datetime import datetime

from fastcs_bacnet.diagnostics.FastCS.queue_probe import QueueStatsProbe


class QueueTracker:
    fastcs_start_time: datetime | None = None
    first_queue_time: datetime | None = None
    first_overflow_time: datetime | None = None
    last_overflow_time: datetime | None = None

    recent_queue_history: list[tuple[int, datetime]]
    history_size: int
    poll_period: float
    total_lost_requests: int = 0

    def __init__(
        self, fastcs_coroutine=None, poll_rate: float = 1.0, history_size: int = 20
    ):
        self.fastcs_coroutine = fastcs_coroutine
        self.poll_period = poll_rate
        self.history_size = history_size
        self.probe = QueueStatsProbe()

    async def start(self):

        if self.fastcs_coroutine is not None:
            self.fastcs_start_time = datetime.now()
            asyncio.create_task(self.fastcs_coroutine())

        while True:
            self.poll()
            await asyncio.sleep(self.poll_period)

    def poll(self):
        queue_stats_data = self.probe.get_stats()
        stats_time = datetime.now()

        self.recent_queue_history.append((queue_stats_data.queue_length[0], stats_time))

        while len(self.recent_queue_history) > self.history_size:
            self.recent_queue_history.pop(0)

        if self.first_queue_time is None and queue_stats_data.queue_length[0] > 0:
            self.first_queue_time = stats_time

        if queue_stats_data.queue_overflow[0] != self.total_lost_requests:
            self.last_overflow_time = stats_time
            # not sure if the queue stats data gives total overflows
            # or current overflows
            self.total_lost_requests = queue_stats_data.queue_overflow[0]

            if self.first_overflow_time is None:
                self.first_overflow_time = stats_time

    def set_fastcs_start_time(self, fastcs_start_time: datetime):
        if self.fastcs_coroutine is not None:
            print("start time will be set when start method is run")
            return
        if self.fastcs_start_time is not None:
            print("start time already set")
            return
        self.fastcs_start_time = fastcs_start_time
