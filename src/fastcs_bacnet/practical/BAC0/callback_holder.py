import asyncio
from collections.abc import Callable, Coroutine
from inspect import iscoroutinefunction
from typing import Any, TypeGuard


class CallbackHolder:
    """
    A class to store a list of callbacks (functions or coroutines) for
    object subscriptions
    Adding callbacks that manipulate common state is undefined behaviour
    """

    type SyncCallback = Callable[[str, Any], None]
    type AsyncCallback = Callable[[str, Any], Coroutine[None, None, None]]
    type Callback = SyncCallback | AsyncCallback

    _sync_callbacks: list[SyncCallback]
    _async_callbacks: list[AsyncCallback]

    _next_callback_index: int = 0
    _callback_dict: dict[int, Callback]

    def __init__(self):
        self._sync_callbacks = []
        self._async_callbacks = []
        self._callback_dict = {}

    def add(self, f: Callback) -> int:
        """
        Adds a callback function / coroutine to the stack

        Returns a "key" (int) for the callback that is added so
        it can be fetched or removed later
        """

        if self.is_sync_callback(f):
            self._sync_callbacks.append(f)
        # required for Pyright to infer f's type
        elif self.is_async_callback(f):
            self._async_callbacks.append(f)
        else:
            print("Callback is neither sync or async??")

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

        if self.is_sync_callback(callback_instance):
            if callback_instance in self._sync_callbacks:
                self._sync_callbacks.remove(callback_instance)
            else:
                print("Sync callback in dict but not in list, this should not happen")
        elif self.is_async_callback(callback_instance):
            if callback_instance in self._async_callbacks:
                self._async_callbacks.remove(callback_instance)
            else:
                print("Async callback in dict but not in list, this should not happen")

    def remove_all(self):
        self._sync_callbacks = []
        self._async_callbacks = []

    async def run_callbacks(self, property_identifier: str, property_value: Any):
        """
        Calls all callbacks added to the holder

        First iterates through coroutines and creates a task for each
        Then iterates through synchronous functions and calls them
        one by one
        """

        for sync_callback in self._sync_callbacks:
            try:
                sync_callback(property_identifier, property_value)
            except BaseException as e:
                print("excepted in synchronous task")
                print(e)

        async with asyncio.TaskGroup() as group:
            for async_callback in self._async_callbacks:
                try:
                    group.create_task(
                        async_callback(property_identifier, property_value)
                    )
                except BaseException as e:
                    print("excepted in asynchronous task")
                    print(e)

    # seems silly to have 2 inverse functions but they are necessary as they are guards
    def is_sync_callback(self, callback: Callback) -> TypeGuard[SyncCallback]:
        return not iscoroutinefunction(callback)

    def is_async_callback(self, callback: Callback) -> TypeGuard[AsyncCallback]:
        return iscoroutinefunction(callback)
