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
    event = AgentEvent(
        event_type="task_queued",
        task_id="task-1",
        message="queued",
        payload={"goal": "Research"},
    )
    queue = manager.subscribe("task-1")
    await manager.publish(event)

    assert await queue.get() == event

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


@pytest.mark.asyncio
async def test_failed_task_releases_concurrency_slot() -> None:
    manager = TaskManager(max_concurrent_tasks=1)
    started: list[str] = []

    async def fail(cancellation_event: asyncio.Event) -> None:
        started.append("first")
        raise RuntimeError("worker failed")

    async def succeed(cancellation_event: asyncio.Event) -> str:
        started.append("second")
        return "done"

    first = manager.submit("first", fail)
    second = manager.submit("second", succeed)

    with pytest.raises(RuntimeError, match="worker failed"):
        await first
    assert await second == "done"
    assert started == ["first", "second"]
    await manager.shutdown()
    assert manager.active_task_count == 0


@pytest.mark.asyncio
async def test_third_task_waits_and_queued_cancel_never_starts() -> None:
    manager = TaskManager(max_concurrent_tasks=2)
    gate = asyncio.Event()
    started: list[str] = []

    async def work(name: str, _: asyncio.Event) -> str:
        started.append(name)
        await gate.wait()
        return name

    first = manager.submit("one", lambda event: work("one", event))
    second = manager.submit("two", lambda event: work("two", event))
    third = manager.submit("three", lambda event: work("three", event))
    await asyncio.sleep(0)
    assert started == ["one", "two"]
    assert manager.cancel("three") is True
    gate.set()
    assert await asyncio.gather(first, second) == ["one", "two"]
    with pytest.raises(asyncio.CancelledError):
        await third
    assert started == ["one", "two"]
    await manager.shutdown()


@pytest.mark.asyncio
async def test_subscribers_receive_same_event_without_slow_client_blocking() -> None:
    manager = TaskManager(max_concurrent_tasks=2)
    first = manager.subscribe("task-1")
    slow = manager.subscribe("task-1")
    event = AgentEvent(
        event_type="task_queued", task_id="task-1", payload={"goal": "x"}
    )
    await manager.publish(event)
    await manager.publish(event)
    assert await first.get() == event
    assert await slow.get() == event
    assert first.maxsize == slow.maxsize == 1
    manager.unsubscribe("task-1", first)
    assert manager.subscriber_count("task-1") == 1
    await manager.shutdown()
