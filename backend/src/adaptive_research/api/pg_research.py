"""The six research routes backed only by committed PostgreSQL state."""

import asyncio
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from adaptive_research.agent.events import AgentEvent
from adaptive_research.agent.state import DecisionContext, ResearchReport
from adaptive_research.api.schemas.research import (
    ResearchCreateRequest,
    ResearchTaskResponse,
)
from adaptive_research.infrastructure.pg_store import (
    TERMINAL,
    CapacityFull,
    EventRecord,
    IdempotencyConflict,
    PgStore,
    TaskRecord,
)

router = APIRouter(prefix="/api/research", tags=["research"])
# P-03 replaces this local-only identity with authenticated account sessions.
LOCAL_OWNER_ID = "p01-local-owner"


class PgCancelResponse(BaseModel):
    task_id: str
    cancelled: bool
    cancellation_requested: bool


class PgTaskResponse(ResearchTaskResponse):
    cancellation_requested: bool
    decision_context: DecisionContext | None = None


def _store(request: Request) -> PgStore:
    return request.app.state.pg_store


def _task_response(task: TaskRecord) -> PgTaskResponse:
    return PgTaskResponse(
        id=task.id,
        goal=task.goal,
        status=task.status,
        error_message=task.error_message,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completion_level=task.completion_level,
        stop_reason=task.stop_reason,
        report=ResearchReport.model_validate(task.report) if task.report else None,
        cancellation_requested=task.cancellation_requested,
        decision_context=task.decision_context,
    )


def _agent_event(event: EventRecord) -> AgentEvent:
    return AgentEvent(
        event_id=str(UUID(int=event.id)),
        task_id=event.task_id,
        event_type=event.event_type,
        step=event.step,
        timestamp=event.created_at,
        message=event.message,
        payload=event.payload,
    )


@router.post("", response_model=PgTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_research(
    body: ResearchCreateRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> PgTaskResponse:
    settings = request.app.state.settings
    if settings.deepseek_api_key is None:
        raise HTTPException(503, "DeepSeek provider is not configured")
    try:
        options = {}
        if idempotency_key is not None:
            options["idempotency_key"] = idempotency_key
        if body.decision_context is not None:
            options["decision_context"] = body.decision_context
        task = await _store(request).create_task(LOCAL_OWNER_ID, body.goal, **options)
    except CapacityFull as exc:
        raise HTTPException(
            status_code=429,
            detail="Research capacity is full",
            headers={"Retry-After": "2"},
        ) from exc
    except IdempotencyConflict as exc:
        raise HTTPException(409, "Idempotency key belongs to another request") from exc
    except ValueError as exc:
        raise HTTPException(422, "Invalid research request") from exc
    return _task_response(task)


@router.get("", response_model=list[PgTaskResponse])
async def list_research(request: Request) -> list[PgTaskResponse]:
    tasks = await _store(request).list_tasks(LOCAL_OWNER_ID)
    return [_task_response(task) for task in tasks]


@router.get("/{task_id}", response_model=PgTaskResponse)
async def get_research(task_id: str, request: Request) -> PgTaskResponse:
    task = await _store(request).get_task(LOCAL_OWNER_ID, task_id)
    if task is None:
        raise HTTPException(404, "Research task not found")
    return _task_response(task)


@router.get("/{task_id}/traces", response_model=list[AgentEvent])
async def list_research_traces(task_id: str, request: Request) -> list[AgentEvent]:
    events = await _store(request).list_events(LOCAL_OWNER_ID, task_id)
    if events is None:
        raise HTTPException(404, "Research task not found")
    return [_agent_event(event) for event in events]


@router.post("/{task_id}/cancel", response_model=PgCancelResponse)
async def cancel_research(task_id: str, request: Request) -> PgCancelResponse:
    task = await _store(request).request_cancel(LOCAL_OWNER_ID, task_id)
    if task is None:
        raise HTTPException(404, "Research task not found")
    return PgCancelResponse(
        task_id=task.id,
        cancelled=task.status == "cancelled",
        cancellation_requested=task.cancellation_requested,
    )


@router.get("/{task_id}/events", response_class=StreamingResponse)
async def stream_research_events(
    task_id: str,
    request: Request,
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
) -> StreamingResponse:
    store = _store(request)
    if await store.get_task(LOCAL_OWNER_ID, task_id) is None:
        raise HTTPException(404, "Research task not found")
    cursor = 0
    if last_event_id is not None:
        try:
            cursor = UUID(last_event_id).int
        except ValueError as exc:
            raise HTTPException(422, "Unknown Last-Event-ID") from exc
        if cursor < 1 or cursor > (1 << 63) - 1:
            raise HTTPException(422, "Unknown Last-Event-ID")
        previous = await store.list_events(LOCAL_OWNER_ID, task_id, cursor - 1)
        if not previous or previous[0].id != cursor:
            raise HTTPException(422, "Unknown Last-Event-ID")

    async def events() -> AsyncIterator[str]:
        nonlocal cursor
        while True:
            try:
                committed = await store.list_events(LOCAL_OWNER_ID, task_id, cursor)
                if committed is None:
                    return
                for row in committed:
                    event = _agent_event(row)
                    cursor = row.id
                    yield (
                        f"id: {event.event_id}\n"
                        f"event: {event.event_type}\n"
                        f"data: {event.model_dump_json()}\n\n"
                    )
                    if row.event_type == "task_finished":
                        return
                if committed:
                    continue
                task = await store.get_task(LOCAL_OWNER_ID, task_id)
                if task is None:
                    return
                if task.status in TERMINAL:
                    # Completion can commit between the event read and task
                    # read. Recheck after observing the terminal row.
                    if await store.list_events(LOCAL_OWNER_ID, task_id, cursor):
                        continue
                    return
            except (SQLAlchemyError, OSError):
                yield "event: service_unavailable\ndata: {}\n\n"
                return
            await asyncio.sleep(0.25)

    return StreamingResponse(events(), media_type="text/event-stream")
