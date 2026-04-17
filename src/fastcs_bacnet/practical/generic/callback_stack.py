import asyncio
from collections.abc import Callable, Coroutine
from inspect import iscoroutinefunction
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

    def add_to_stack(self, f: Callback) -> int:

        if iscoroutinefunction(f):
            self.async_callbacks.append(f)
        elif callable(f):
            # We know f must be a normal callable function here (not a coroutine)
            # as the previous if establishes it is not a coroutine
            # Pylance does not pick this up though
            self.sync_callbacks.append(f)  # type: ignore

        callback_key = self.next_callback_index
        self.next_callback_index += 1

        self.callback_dict[callback_key] = f

        return callback_key

    def get_callback(self, key: int) -> Callback | None:
        if key not in self.callback_dict:
            return None
        return self.callback_dict[key]

    def remove_callback(self, key: int):
        self.callback_dict.pop(key)

    def sum_callback(self, *args: P.args, **kwargs: P.kwargs):

        for async_callback in self.async_callbacks:
            task = asyncio.create_task(async_callback(*args, **kwargs))
            self.in_progress_callbacks.add(task)
            task.add_done_callback(self.in_progress_callbacks.discard)

        for sync_callback in self.sync_callbacks:
            sync_callback(*args, **kwargs)
