import asyncio
import logging
from collections.abc import Coroutine
from typing import Any, TypeVar

LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


def create_logged_task(coro: Coroutine[Any, Any, T], name: str) -> asyncio.Task[T]:
    task = asyncio.create_task(coro, name=name)
    task.add_done_callback(_log_task_exception)
    return task


def _log_task_exception(task: asyncio.Task[Any]) -> None:
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        LOGGER.error("%s: Task exited with unhandled exception: %r", task.get_name(), exc)
