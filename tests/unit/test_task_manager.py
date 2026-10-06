import asyncio

import pytest

from adaptive_agent.events import AgentEvent
from adaptive_agent.runtime.task_manager import TaskManager


@pytest.mark.asyncio
async def test_task_manager_limits_concurrency() -> None:
    manager = TaskManager(max_concurrent_tasks=1)
    gate = asyncio.Event()
    started: list[str] = []

    async def work(name: str, cancellation_event: asyncio.Event) -> str:
        assert cancellation_event.is_set() is False
        started.append(name)
        await gate.wait()
        return name

    first = manager.submit("one", lambda event: work("one", event))
    second = manager.submit("two", lambda event: work("two", event))
    await asyncio.sleep(0)

    assert started == ["one"]
    gate.set()
    assert await asyncio.gather(first, second) == ["one", "two"]


@pytest.mark.asyncio
async def test_task_manager_publishes_and_cancels() -> None:
    manager = TaskManager(max_concurrent_tasks=1)
    event = AgentEvent(type="step", task_id="task-1", message="queued")
    await manager.publish(event)

    assert await manager.event_queue("task-1").get() == event

    started = asyncio.Event()

    async def wait_for_cancellation(cancellation_event: asyncio.Event) -> str:
        started.set()
        await cancellation_event.wait()
        return "cancelled"

    task = manager.submit("task-1", wait_for_cancellation)
    await started.wait()
    assert manager.cancel("task-1") is True
    assert await task == "cancelled"
    await asyncio.sleep(0)
    assert manager.active_task_count == 0
