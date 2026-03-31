import asyncio
from datetime import datetime

from fastcs_bacnet.diagnostics.FastCS.queue_probe import QueueStatsProbe


class QueueTracker:
    """
    Tracks the EPICS CA request queue whilst a fastcs function is running
    Used to get diagnostic data
    Stores a list of the recent queue lengths
    Can alsp give start up time and time to queue overflow
    """

    _fastcs_start_time: datetime | None = None
    _first_queue_time: datetime | None = None
    _first_overflow_time: datetime | None = None
    _last_overflow_time: datetime | None = None

    _recent_queue_history: list[tuple[int, datetime]]
    _history_size: int
    _poll_period: float
    _total_lost_requests: int = 0

    def __init__(
        self, fastcs_coroutine=None, poll_peroid: float = 1.0, history_size: int = 20
    ):
        """
        fastcs_coroutine: the coroutine that starts the fastcs application
            This can be left as None if you dont want to start the
            application in this class, the tracker can be run separetely
            If the coroutine is set the fastcs application will be started when
            this objects start() method is run
            this will also record the fastcs start time
            If the fastcs application is run separately, set its start time using
            the set_fastcs_start_time() method
        poll_period: Time between polling the EPICS CA queue
        history_size: maximum length of the recent_queue_history list
            Number of queue length values to store at once
        """
        self._fastcs_coroutine = fastcs_coroutine
        self._poll_period = poll_peroid
        self._history_size = history_size
        self._probe = QueueStatsProbe()

    async def start(self):
        """
        Starts the polling loop
        If a fastcs coroutine is given it starts this too and records the time
        """

        if self._fastcs_coroutine is not None:
            self._fastcs_start_time = datetime.now()
            asyncio.create_task(self._fastcs_coroutine())

        while True:
            self.poll()
            await asyncio.sleep(self._poll_period)

    def poll(self):
        """
        Checks the EPICS CA queue length and records the value
        (as well as the time of recording) and prunes the queue to size
        Checks if this was the first non-zero queue size and checks for overflows
        """
        queue_stats_data = self._probe.get_stats()
        stats_time = datetime.now()

        self._recent_queue_history.append(
            (queue_stats_data.queue_length[0], stats_time)
        )

        while len(self._recent_queue_history) > self._history_size:
            self._recent_queue_history.pop(0)

        if self._first_queue_time is None and queue_stats_data.queue_length[0] > 0:
            self._first_queue_time = stats_time

        if queue_stats_data.queue_overflow[0] != self._total_lost_requests:
            self._last_overflow_time = stats_time
            # not sure if the queue stats data gives total overflows
            # or current overflows
            self._total_lost_requests = queue_stats_data.queue_overflow[0]

            if self._first_overflow_time is None:
                self._first_overflow_time = stats_time

    def set_fastcs_start_time(self, fastcs_start_time: datetime):
        """
        If no fastcs coroutine is given in the constructor we assume a
        fastcs application is being run outside of this object
        If you still want start heuristics (e.g. start up time)
        you can set the fastcs_start_time using this method
        """
        if self._fastcs_coroutine is not None:
            print("start time will be set when start method is run")
            return
        if self._fastcs_start_time is not None:
            print("start time already set")
            return
        self._fastcs_start_time = fastcs_start_time
