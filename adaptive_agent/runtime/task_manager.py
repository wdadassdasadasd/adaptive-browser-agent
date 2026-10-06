"""In-process task, event queue, and concurrency skeleton."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from adaptive_agent.events import AgentEvent

TaskFactory = Callable[[asyncio.Event], Awaitable[Any]]


class TaskManager:
    def __init__(self, max_concurrent_tasks: int) -> None:
        if max_concurrent_tasks < 1:
            raise ValueError("max_concurrent_tasks must be at least 1")
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self._tasks: dict[str, asyncio.Task[Any]] = {}
        self._cancellation_events: dict[str, asyncio.Event] = {}
        self._event_queues: dict[str, asyncio.Queue[AgentEvent]] = {}

    def submit(self, task_id: str, task_factory: TaskFactory) -> asyncio.Task[Any]:
        existing = self._tasks.get(task_id)
        if existing is not None and not existing.done():
            raise ValueError(f"Task is already running: {task_id}")

        cancellation_event = asyncio.Event()
        task = asyncio.create_task(
            self._run(task_factory, cancellation_event), name=f"research:{task_id}"
        )
        self._tasks[task_id] = task
        self._cancellation_events[task_id] = cancellation_event
        self._event_queues.setdefault(task_id, asyncio.Queue())
        task.add_done_callback(
            lambda completed, key=task_id: self._remove_completed(key, completed)
        )
        return task

    async def _run(
        self, task_factory: TaskFactory, cancellation_event: asyncio.Event
    ) -> Any:
        async with self._semaphore:
            return await task_factory(cancellation_event)

    def event_queue(self, task_id: str) -> asyncio.Queue[AgentEvent]:
        return self._event_queues.setdefault(task_id, asyncio.Queue())

    async def publish(self, event: AgentEvent) -> None:
        await self.event_queue(event.task_id).put(event)

    def cancel(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task is None or task.done():
            return False
        self._cancellation_events[task_id].set()
        return True

    async def shutdown(self) -> None:
        tasks = list(self._tasks.values())
        for task in tasks:
            if not task.done():
                task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()
        self._cancellation_events.clear()
        self._event_queues.clear()

    @property
    def active_task_count(self) -> int:
        return sum(not task.done() for task in self._tasks.values())

    def _remove_completed(self, task_id: str, completed: asyncio.Task[Any]) -> None:
        if self._tasks.get(task_id) is completed:
            self._tasks.pop(task_id, None)
            self._cancellation_events.pop(task_id, None)
