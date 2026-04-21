from ctypes import POINTER, Structure, c_int, pointer
from dataclasses import dataclass

from epicscorelibs.ioc import dbCore


class CQueueStatsData(Structure):
    _fields_ = [
        ("size", c_int),
        ("numUsed", c_int * 3),
        ("maxUsed", c_int * 3),
        ("numOverflow", c_int * 3),
    ]


@dataclass
class PythonQueueStatsData:
    size: int
    # priority: high, mid, low
    queue_length: tuple[int, int, int]
    max_queue_length: tuple[int, int, int]
    queue_overflow: tuple[int, int, int]


class QueueStatsProbe:
    def __init__(self):
        callback_struct_ptr = POINTER(CQueueStatsData)

        self.callbackQueueStatus = dbCore.callbackQueueStatus
        self.callbackQueueStatus.argtypes = (
            c_int,
            callback_struct_ptr,
        )

    def get_stats(self) -> PythonQueueStatsData:

        foo = CQueueStatsData()
        self.callbackQueueStatus(0, pointer(foo))
        return PythonQueueStatsData(
            foo.size,
            (foo.numUsed[0], foo.numUsed[1], foo.numUsed[2]),
            (foo.maxUsed[0], foo.maxUsed[1], foo.maxUsed[2]),
            (foo.numOverflow[0], foo.numOverflow[1], foo.numOverflow[2]),
        )
