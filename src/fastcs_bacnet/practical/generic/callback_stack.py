import asyncio
from collections.abc import Callable, Coroutine
from typing import Generic, ParamSpec, TypeAlias

P = ParamSpec("P")
Callback: TypeAlias = Callable[P, None] | Callable[P, Coroutine[None, None, None]]


class CallbackStack(Generic[P]):
    sync_callbacks: list[Callable[P, None]]
    async_callbacks: list[Callable[P, Coroutine[None, None, None]]]
    in_progress_callbacks: set[asyncio.Task]

    next_callback_index: int = 0
    callback_dict: dict[int, Callback]

    def __init__(self):
        self.sync_callbacks = []
        self.async_callbacks = []
        self.in_progress_callbacks = set()
        self.callback_dict = {}

    def add_to_stack(self, f: Callback):
        pass

    def get_callback(self, key: int) -> Callback | None:
        pass

    def remove_callback(self, key: int):
        pass

    def sum_callback(self, *args: P.args, **kwargs: P.kwargs):
        pass
