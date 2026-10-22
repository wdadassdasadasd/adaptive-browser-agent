"""Application service joining task scheduling, AgentLoop, and persistence."""

import asyncio
from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from adaptive_research.agent.adapters.browser_use_adapter import BrowserUseAdapter
from adaptive_research.agent.agent_loop import AgentLoop
from adaptive_research.agent.events import AgentEvent
from adaptive_research.agent.llm.deepseek import DeepSeekClient
from adaptive_research.agent.runtime.task_manager import TaskManager
from adaptive_research.agent.tools.github_tool import GitHubTool
from adaptive_research.agent.tools.router import ToolRouter
from adaptive_research.infrastructure.config import Settings
from adaptive_research.infrastructure.db.models import ResearchTaskModel
from adaptive_research.infrastructure.persistence import TERMINAL, PersistenceService


class MissingProviderKeyError(Exception):
    """A new task cannot start without a configured DeepSeek credential."""


class ResearchService:
    def __init__(
        self,
        settings: Settings,
        sessions: async_sessionmaker[AsyncSession],
        agent_factory: Callable[[], AgentLoop] | None = None,
    ) -> None:
        self.settings = settings
        self.sessions = sessions
        self.manager = TaskManager(settings.max_concurrent_tasks)
        self.agent_factory = agent_factory or self._new_agent
        self._shutting_down = False

    @property
    def _secrets(self) -> tuple[str, ...]:
        return tuple(
            secret.get_secret_value()
            for secret in (self.settings.deepseek_api_key, self.settings.github_token)
            if secret is not None
        )

    def _persistence(self, session: AsyncSession) -> PersistenceService:
        return PersistenceService(session, self._secrets)

    def _new_agent(self) -> AgentLoop:
        provider = DeepSeekClient(
            self.settings.deepseek_api_key.get_secret_value()
            if self.settings.deepseek_api_key
            else None,
            model=self.settings.deepseek_model,
        )
        browser = BrowserUseAdapter()
        github = GitHubTool(
            token=self.settings.github_token.get_secret_value()
            if self.settings.github_token
            else None
        )
        return AgentLoop(
            provider, ToolRouter(browser, github), max_steps=self.settings.max_steps
        )

    async def recover(self) -> int:
        async with self.sessions() as session:
            return await self._persistence(session).finalize_unfinished()

    async def create(self, goal: str) -> ResearchTaskModel:
        if self.settings.deepseek_api_key is None:
            raise MissingProviderKeyError
        async with self.sessions() as session:
            task = await self._persistence(session).create_task(goal)
        self.manager.submit(
            task.id, lambda cancel: self._execute(task.id, goal, cancel)
        )
        return task

    async def _execute(
        self, task_id: str, goal: str, cancellation: asyncio.Event
    ) -> None:
        async def on_event(event: AgentEvent) -> None:
            if self._shutting_down:
                # Shutdown cancels the in-process runner. Recovery must classify
                # its persisted evidence as server_restart, not user_cancelled.
                return
            async with self.sessions() as session:
                row = await self._persistence(session).record_event(event)
            if row is None and event.event_type == "task_started":
                raise asyncio.CancelledError
            if row is not None:
                await self.manager.publish(event)

        try:
            agent = self.agent_factory()
            await agent.run(
                goal, cancellation=cancellation, task_id=task_id, on_event=on_event
            )
        except asyncio.CancelledError:
            # Queued tasks are terminalized by cancel(); running tasks by AgentLoop.
            pass
        except Exception:  # noqa: BLE001 - persist a terminal failure for unexpected runner errors
            failure = AgentEvent(
                event_type="task_finished",
                task_id=task_id,
                payload={
                    "status": "failed",
                    "completion_level": "none",
                    "stop_reason": "execution_error",
                },
            )
            await on_event(failure)

    async def get(self, task_id: str) -> ResearchTaskModel | None:
        async with self.sessions() as session:
            return await self._persistence(session).get_task(task_id)

    async def list(self) -> list[ResearchTaskModel]:
        async with self.sessions() as session:
            return await self._persistence(session).list_tasks()

    async def report(self, task_id: str):
        async with self.sessions() as session:
            return await self._persistence(session).report_for_task(task_id)

    async def traces(self, task_id: str, after_id: int = 0):
        async with self.sessions() as session:
            service = self._persistence(session)
            return await service.get_task_traces(task_id, after_id)

    async def trace_id_for_event(self, task_id: str, event_id: str) -> int | None:
        async with self.sessions() as session:
            return await self._persistence(session).trace_id_for_event(
                task_id, event_id
            )

    async def cancel(self, task_id: str) -> bool | None:
        task = await self.get(task_id)
        if task is None:
            return None
        if task.status in {"completed", "partial", "failed", "cancelled"}:
            return task.status == "cancelled"
        if task.status == "queued":
            event = AgentEvent(
                event_type="task_finished",
                task_id=task_id,
                payload={
                    "status": "cancelled",
                    "completion_level": "none",
                    "stop_reason": "user_cancelled",
                },
            )
            async with self.sessions() as session:
                row = await self._persistence(session).cancel_queued(task_id, event)
            if row is not None:
                self.manager.cancel(task_id)
                await self.manager.publish(event)
                return True
        if self.manager.cancel(task_id):
            # The runner may have committed a terminal status after our first read
            # while its asyncio task has not returned yet.
            current = await self.get(task_id)
            if current is not None and current.status in TERMINAL:
                return current.status == "cancelled"
            return True
        current = await self.get(task_id)
        return current is not None and current.status == "cancelled"

    async def shutdown(self) -> None:
        self._shutting_down = True
        await self.manager.shutdown()
        await self.recover()
