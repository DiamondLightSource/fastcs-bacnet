import asyncio
from collections.abc import Callable, Coroutine
from inspect import iscoroutinefunction
from typing import Any, TypeGuard

type SyncCovCallback = Callable[[str, float | bool], None]
type AsyncCovCallback = Callable[[str, float | bool], Coroutine[None, None, None]]
type CovCallback = SyncCovCallback | AsyncCovCallback


class DictListCallbackMismatchError(Exception):
    pass


class CovCallbackHolder:
    """
    Stores callback functions and coroutines that run when a CoV update is recieved
    from an object subscription

    All callbacks must take 2 parameters:
    A string for representing the property identifier
    And a value of Any type to represent the new property value
    """

    _sync_callbacks: list[SyncCovCallback]
    _async_callbacks: list[AsyncCovCallback]

    _next_callback_key: int = 0

    # Stores all callbacks with their assigned key
    _callback_dict: dict[int, CovCallback]

    def __init__(self):
        self._sync_callbacks = []
        self._async_callbacks = []
        self._callback_dict = {}

    def add(self, callback: CovCallback) -> int:
        """
        Adds a callback function / coroutine to the holder

        Returns a "key" (int) to reference the callback later
        for getting or removing
        """

        if self.is_sync_callback(callback):
            self._sync_callbacks.append(callback)
        # required for Pyright to infer f's type
        elif self.is_async_callback(callback):
            self._async_callbacks.append(callback)
        else:
            # TODO: change this to logging
            raise ValueError

        callback_key = self._next_callback_key
        self._next_callback_key += 1

        self._callback_dict[callback_key] = callback

        return callback_key

    def get(self, key: int) -> CovCallback:
        """
        Returns callback

        key: corresponding key to the callback
        """
        if key not in self._callback_dict:
            # TODO: replace with logging
            raise KeyError
        return self._callback_dict[key]

    def remove(self, key: int):
        """
        Removes a callback

        key: corresponding key to the callback
        """
        callback_instance = self._callback_dict.pop(key)

        if self.is_sync_callback(callback_instance):
            if callback_instance in self._sync_callbacks:
                self._sync_callbacks.remove(callback_instance)
            else:
                raise DictListCallbackMismatchError(
                    "Sync callback in dict but not in list"
                )
        elif self.is_async_callback(callback_instance):
            if callback_instance in self._async_callbacks:
                self._async_callbacks.remove(callback_instance)
            else:
                raise DictListCallbackMismatchError(
                    "Async callback in dict but not in list"
                )

    def remove_all(self):
        self._sync_callbacks = []
        self._async_callbacks = []
        self._callback_dict = {}

    async def run_callbacks(self, property_identifier: str, property_value: Any):
        """
        Calls all callbacks added to the holder

        This should be called when a CoV update is recieved
        """

        for sync_callback in self._sync_callbacks:
            try:
                sync_callback(property_identifier, property_value)
            except BaseException as e:
                # TODO: log error here
                print("excepted in synchronous task")
                print(e)

        async with asyncio.TaskGroup() as group:
            for async_callback in self._async_callbacks:
                try:
                    group.create_task(
                        async_callback(property_identifier, property_value)
                    )
                except BaseException as e:
                    # TODO: log error here
                    print("excepted in asynchronous task")
                    print(e)

    # seems silly to have 2 inverse functions but they are necessary as they are guards
    def is_sync_callback(self, callback: CovCallback) -> TypeGuard[SyncCovCallback]:
        return not iscoroutinefunction(callback)

    def is_async_callback(self, callback: CovCallback) -> TypeGuard[AsyncCovCallback]:
        return iscoroutinefunction(callback)
