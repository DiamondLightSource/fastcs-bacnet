import asyncio
from collections.abc import Callable, Coroutine
from inspect import iscoroutinefunction


class CallbackHolder:
    """
    A class to store a list of callbacks (functions or coroutines) for device variables
    Adding callbacks that manipulate common state is undefined behaviour
    """

    type SyncCallback = Callable[[float, float | None], None]
    type AsyncCallback = Callable[[float, float | None], Coroutine[None, None, None]]
    type Callback = SyncCallback | AsyncCallback

    _sync_callbacks: list[SyncCallback]
    _async_callbacks: list[AsyncCallback]
    _in_progress_callbacks: set[asyncio.Task]

    _next_callback_index: int = 0
    _callback_dict: dict[int, Callback]

    def __init__(self):
        self._sync_callbacks = []
        self._async_callbacks = []
        self._in_progress_callbacks = set()
        self._callback_dict = {}

    def add(self, f: Callback) -> int:
        """
        Adds a callback function / coroutine to the stack
        Returns a "key" (int) for the callback that is added so
        it can be fetched or removed later
        """

        if iscoroutinefunction(f):
            self._async_callbacks.append(f)
        elif callable(f):
            # We know f must be a normal callable function here (not a coroutine)
            # as the previous if establishes it is not a coroutine
            # Pylance does not pick this up though
            self._sync_callbacks.append(f)  # type: ignore

        callback_key = self._next_callback_index
        self._next_callback_index += 1

        self._callback_dict[callback_key] = f

        return callback_key

    def get(self, key: int) -> Callback | None:
        """
        Returns callback when given the key
        """
        if key not in self._callback_dict:
            return None
        return self._callback_dict[key]

    def remove(self, key: int):
        """
        Removes a callback when given the key
        """
        callback_instance = self._callback_dict.pop(key)

        if callback_instance in self._sync_callbacks:
            # If calback instance is in _sync_callbacks it must be a SyncCallback
            # Pyright cant tell this so type is ignored
            self._sync_callbacks.remove(callback_instance)  # type: ignore
        elif callback_instance in self._async_callbacks:
            # If calback instance is in _async_callbacks it must be an AsyncCallback
            # Pyright cant tell this so type is ignored
            self._async_callbacks.remove(callback_instance)  # type: ignore

    def sum_callback(self, new_value: float, previous_value: float | None):
        """
        Calls all callbacks added to the holder
        First iterates through coroutines and creates a task for each
        Then iterates through synchronous functions and calls them
        one by one
        """

        for async_callback in self._async_callbacks:
            task = asyncio.create_task(async_callback(new_value, previous_value))
            self._in_progress_callbacks.add(task)
            task.add_done_callback(self._in_progress_callbacks.discard)

        for sync_callback in self._sync_callbacks:
            sync_callback(new_value, previous_value)

    def remove_all(self):
        # could this cause memory leaks??
        self._sync_callbacks = []
        self._async_callbacks = []
