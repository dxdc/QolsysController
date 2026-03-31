from collections.abc import Callable
from typing import Any

from qolsys_controller.enum import QolsysEvent
from collections.abc import Callable, Awaitable
from typing import Any, Union

import inspect
import asyncio


class Event:
    def __init__(self, type: QolsysEvent, source: object, data: dict[str, Any]) -> None:
        self.type: QolsysEvent = type
        self.data = data
        self.source = source


Callback = Callable[[Event], Union[None, Awaitable[None]]]


class QolsysObservable_v3:
    def __init__(self) -> None:
        self._observers: dict[QolsysEvent, list[Callback]] = {}
        self._batch_update_active = False
        self._batch_update_data: dict[QolsysEvent, dict[str, Any]] = {}

    def register(self, notification: QolsysEvent, callback: Callable[[Event], None]) -> None:
        callbacks = self._observers.setdefault(notification, [])
        if callback not in callbacks:
            callbacks.append(callback)

    def unregister(self, event: QolsysEvent, callback: Callable[[Event], None]) -> None:
        if event in self._observers and callback in self._observers[event]:
            self._observers[event].remove(callback)

    async def notify(self, event: Event) -> None:
        if self._batch_update_active:
            event_dict = self._batch_update_data.get(event.type, {})
            event_dict.update(event.data)
            self._batch_update_data[event.type] = event_dict
        else:
            for callback in self._observers.get(event.type, []):
                if inspect.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)

    def start_batch_update(self) -> None:
        self._batch_update_data.clear()
        self._batch_update_active = True

    def end_batch_update(self) -> None:
        self._batch_update_active = False
        for event_type, event_data in self._batch_update_data.items():
            event = Event(type=event_type, source=self, data=event_data)
            for callback in self._observers.get(event_type, []):
                callback(event)
        self._batch_update_data.clear()

    def cancel_batch_update(self) -> None:
        self._batch_update_active = False
        self._batch_update_data.clear()
