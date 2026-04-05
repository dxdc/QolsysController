import asyncio
import inspect
from collections.abc import Awaitable
from typing import Any, Coroutine, Protocol, cast

from qolsys_controller.enum import QolsysNotification

CallbackResult = None | Awaitable[None]


class Callback(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> CallbackResult: ...


class Event:
    def __init__(self, notification: QolsysNotification, source: object, data: dict[str, Any] | None = None) -> None:
        self.type: QolsysNotification = notification
        self.data = data or {}
        self.source = source


class QolsysObservable_v3:
    def __init__(self) -> None:
        self._observers: dict[QolsysNotification, list[Callback]] = {}
        self._batch_update_active = False
        self._batch_update_data: dict[QolsysNotification, dict[str, Any]] = {}

    def register(self, notification: QolsysNotification, callback: Callback) -> None:
        callbacks = self._observers.setdefault(notification, [])
        if callback not in callbacks:
            callbacks.append(callback)

    def unregister(self, notification: QolsysNotification, callback: Callback) -> None:
        if notification in self._observers and callback in self._observers[notification]:
            self._observers[notification].remove(callback)

    def _invoke_callback(self, callback: Callback, event: Event) -> CallbackResult:
        try:
            signature = inspect.signature(callback)
        except (TypeError, ValueError):
            return callback(event)

        has_varargs = any(parameter.kind == inspect.Parameter.VAR_POSITIONAL for parameter in signature.parameters.values())
        positional_parameters = [
            parameter
            for parameter in signature.parameters.values()
            if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        ]

        if has_varargs or positional_parameters:
            return callback(event)

        return callback()

    def _dispatch_callback(self, callback: Callback, event: Event) -> None:
        result = self._invoke_callback(callback, event)
        if inspect.isawaitable(result):
            try:
                asyncio.ensure_future(result)
            except RuntimeError:
                asyncio.run(cast(Coroutine[Any, Any, None], result))

    def notify(self, event: Event) -> None:
        notification = event.type

        if self._batch_update_active:
            event_dict = self._batch_update_data.get(event.type, {})
            event_dict.update(event.data)
            self._batch_update_data[event.type] = event_dict
        else:
            for callback in self._observers.get(notification, []):
                self._dispatch_callback(callback, event)

    def start_batch_update(self) -> None:
        self._batch_update_data.clear()
        self._batch_update_active = True

    def end_batch_update(self) -> None:
        self._batch_update_active = False
        for event_type, event_data in self._batch_update_data.items():
            event = Event(notification=event_type, source=self, data=event_data)
            for callback in self._observers.get(event_type, []):
                self._dispatch_callback(callback, event)
        self._batch_update_data.clear()

    def cancel_batch_update(self) -> None:
        self._batch_update_active = False
        self._batch_update_data.clear()
