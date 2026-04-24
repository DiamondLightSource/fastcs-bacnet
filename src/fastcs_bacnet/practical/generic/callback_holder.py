import asyncio
from collections.abc import Callable, Coroutine
from inspect import iscoroutinefunction

# *P here is a TypeVarTuple, It represents a generic tuple of types
# E.g. [str, int, float] or [int]
# Callbacks added to the holder must take arguments of these types


# Ideally we would use a ParamSpec here (**P) instead
# However, Pyright doesnt like it when you unpack tuples into a ParamSpec
# So this method works better if you want to use type aliases
class CallbackHolder[*P]:
    """
    A generic class to store a list of callbacks (functions or coroutines) for
    some other object
    The type parameters should be set to the arguments the callbacks expect
    Adding callbacks that manipulate common state is undefined behaviour
    """

    type SyncCallback = Callable[[*P], None]
    type AsyncCallback = Callable[[*P], Coroutine[None, None, None]]
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
        self._callback_dict.pop(key)

    def sum_callback(self, *args: *P):
        """
        This is the callback function that calls all added callbacks
        First iterates through coroutines and creates a task for each
        Then iterates through synchronous functions and calls them
        one by one
        """

        for async_callback in self._async_callbacks:
            task = asyncio.create_task(async_callback(*args))
            self._in_progress_callbacks.add(task)
            task.add_done_callback(self._in_progress_callbacks.discard)

        for sync_callback in self._sync_callbacks:
            sync_callback(*args)
