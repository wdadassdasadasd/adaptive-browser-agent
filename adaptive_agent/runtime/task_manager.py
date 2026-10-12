"""In-process task scheduling, cancellation, and bounded event notifications."""

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
        self._running: set[str] = set()
        self._subscribers: dict[str, set[asyncio.Queue[AgentEvent]]] = {}

    def submit(self, task_id: str, task_factory: TaskFactory) -> asyncio.Task[Any]:
        existing = self._tasks.get(task_id)
        if existing is not None and not existing.done():
            raise ValueError(f"Task is already running: {task_id}")

        cancellation_event = asyncio.Event()
        task = asyncio.create_task(
            self._run(task_id, task_factory, cancellation_event),
            name=f"research:{task_id}",
        )
        self._tasks[task_id] = task
        self._cancellation_events[task_id] = cancellation_event
        task.add_done_callback(
            lambda completed, key=task_id: self._remove_completed(key, completed)
        )
        return task

    async def _run(
        self, task_id: str, task_factory: TaskFactory, cancellation_event: asyncio.Event
    ) -> Any:
        async with self._semaphore:
            if cancellation_event.is_set():
                raise asyncio.CancelledError
            self._running.add(task_id)
            try:
                return await task_factory(cancellation_event)
            finally:
                self._running.discard(task_id)

    def event_queue(self, task_id: str) -> asyncio.Queue[AgentEvent]:
        """Compatibility helper for callers that need one subscription."""

        return self.subscribe(task_id)

    def subscribe(self, task_id: str) -> asyncio.Queue[AgentEvent]:
        queue: asyncio.Queue[AgentEvent] = asyncio.Queue(maxsize=1)
        self._subscribers.setdefault(task_id, set()).add(queue)
        return queue

    def unsubscribe(self, task_id: str, queue: asyncio.Queue[AgentEvent]) -> None:
        subscribers = self._subscribers.get(task_id)
        if subscribers is not None:
            subscribers.discard(queue)
            if not subscribers:
                self._subscribers.pop(task_id, None)

    def subscriber_count(self, task_id: str) -> int:
        return len(self._subscribers.get(task_id, ()))

    async def publish(self, event: AgentEvent) -> None:
        for queue in tuple(self._subscribers.get(event.task_id, ())):
            if not queue.full():
                queue.put_nowait(event)

    def cancel(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task is None or task.done():
            return False
        self._cancellation_events[task_id].set()
        if task_id not in self._running:
            task.cancel()
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
        self._running.clear()
        self._subscribers.clear()

    @property
    def active_task_count(self) -> int:
        return sum(not task.done() for task in self._tasks.values())

    def _remove_completed(self, task_id: str, completed: asyncio.Task[Any]) -> None:
        if self._tasks.get(task_id) is completed:
            self._tasks.pop(task_id, None)
            self._cancellation_events.pop(task_id, None)
        if not completed.cancelled():
            completed.exception()
