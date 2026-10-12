"""Six public research routes backed by the application service."""

from collections.abc import AsyncIterator
from datetime import UTC

import anyio
from fastapi import APIRouter, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from adaptive_agent.events import AgentEvent
from adaptive_agent.state import ResearchReport
from backend.schemas.research import (
    CancelResponse,
    ResearchCreateRequest,
    ResearchTaskResponse,
)
from backend.services.persistence import PersistenceService
from backend.services.research import MissingProviderKeyError, ResearchService

router = APIRouter(prefix="/api/research", tags=["research"])


def _service(request: Request) -> ResearchService:
    return request.app.state.research


async def _response(service: ResearchService, task) -> ResearchTaskResponse:
    traces = await service.traces(task.id)
    terminal = next(
        (trace for trace in reversed(traces) if trace.event_type == "task_finished"),
        None,
    )
    # Status and terminal details must reflect the same committed event when
    # completion lands between the task and trace reads.
    status_value = terminal.payload["status"] if terminal else task.status
    updated_at = terminal.created_at if terminal else task.updated_at
    raw_report = terminal.payload.get("report") if terminal else None
    return ResearchTaskResponse(
        id=task.id,
        goal=task.goal,
        status=status_value,
        error_message=task.error_message,
        created_at=task.created_at.replace(tzinfo=UTC)
        if task.created_at.tzinfo is None
        else task.created_at,
        updated_at=updated_at.replace(tzinfo=UTC)
        if updated_at.tzinfo is None
        else updated_at,
        completion_level=terminal.payload.get("completion_level") if terminal else None,
        stop_reason=terminal.payload.get("stop_reason") if terminal else None,
        report=ResearchReport.model_validate(raw_report) if raw_report else None,
    )


@router.post(
    "", response_model=ResearchTaskResponse, status_code=status.HTTP_202_ACCEPTED
)
async def create_research(
    request: ResearchCreateRequest, http: Request
) -> ResearchTaskResponse:
    service = _service(http)
    try:
        task = await service.create(request.goal)
    except MissingProviderKeyError as exc:
        raise HTTPException(503, "DeepSeek provider is not configured") from exc
    return ResearchTaskResponse(
        id=task.id,
        goal=task.goal,
        status="queued",
        created_at=task.created_at.replace(tzinfo=UTC)
        if task.created_at.tzinfo is None
        else task.created_at,
        updated_at=task.updated_at.replace(tzinfo=UTC)
        if task.updated_at.tzinfo is None
        else task.updated_at,
    )


@router.get("", response_model=list[ResearchTaskResponse])
async def list_research(request: Request) -> list[ResearchTaskResponse]:
    service = _service(request)
    return [await _response(service, task) for task in await service.list()]


@router.get("/{task_id}", response_model=ResearchTaskResponse)
async def get_research(task_id: str, request: Request) -> ResearchTaskResponse:
    service = _service(request)
    task = await service.get(task_id)
    if task is None:
        raise HTTPException(404, "Research task not found")
    return await _response(service, task)


@router.get(
    "/{task_id}/events",
    response_class=StreamingResponse,
    responses={200: {"content": {"text/event-stream": {}}}},
)
async def stream_research_events(
    task_id: str,
    request: Request,
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
) -> StreamingResponse:
    service = _service(request)
    if await service.get(task_id) is None:
        raise HTTPException(404, "Research task not found")
    cursor = 0
    if last_event_id is not None:
        found = await service.trace_id_for_event(task_id, last_event_id)
        if found is None:
            raise HTTPException(422, "Unknown Last-Event-ID")
        cursor = found

    async def events() -> AsyncIterator[str]:
        nonlocal cursor
        queue = service.manager.subscribe(task_id)
        try:
            while True:
                # A disconnected SSE client cancels the response task. Let an
                # in-flight SQLite read close its session before cancellation
                # can tear down the connection.
                with anyio.CancelScope(shield=True):
                    traces = await service.traces(task_id, cursor)
                for trace in traces:
                    event = PersistenceService.trace_event(trace)
                    cursor = trace.id
                    yield (
                        f"id: {event.event_id}\n"
                        f"event: {event.event_type}\n"
                        f"data: {event.model_dump_json()}\n\n"
                    )
                    if event.event_type == "task_finished":
                        return
                if traces:
                    continue
                with anyio.CancelScope(shield=True):
                    task = await service.get(task_id)
                if task is not None and task.status in {
                    "completed",
                    "partial",
                    "failed",
                    "cancelled",
                }:
                    with anyio.CancelScope(shield=True):
                        pending = await service.traces(task_id, cursor)
                    if pending:
                        continue
                    return
                await queue.get()
        finally:
            service.manager.unsubscribe(task_id, queue)

    return StreamingResponse(events(), media_type="text/event-stream")


@router.get("/{task_id}/traces", response_model=list[AgentEvent])
async def list_research_traces(task_id: str, request: Request) -> list[AgentEvent]:
    service = _service(request)
    if await service.get(task_id) is None:
        raise HTTPException(404, "Research task not found")
    return [
        PersistenceService.trace_event(trace) for trace in await service.traces(task_id)
    ]


@router.post("/{task_id}/cancel", response_model=CancelResponse)
async def cancel_research(task_id: str, request: Request) -> CancelResponse:
    cancelled = await _service(request).cancel(task_id)
    if cancelled is None:
        raise HTTPException(404, "Research task not found")
    return CancelResponse(task_id=task_id, cancelled=cancelled)
