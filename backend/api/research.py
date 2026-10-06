"""Research API placeholder routes."""

from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from backend.schemas.research import (
    AgentTraceResponse,
    CancelResponse,
    ResearchCreateRequest,
    ResearchTaskResponse,
)

router = APIRouter(prefix="/api/research", tags=["research"])
NOT_IMPLEMENTED = "Research execution is not implemented in the initialization phase"


async def _empty_event_stream() -> AsyncIterator[str]:
    """Expose the correct SSE transport without simulating runtime events."""

    if False:
        yield ""


@router.post(
    "", response_model=ResearchTaskResponse, status_code=status.HTTP_202_ACCEPTED
)
async def create_research(request: ResearchCreateRequest) -> ResearchTaskResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=NOT_IMPLEMENTED
    )


@router.get("", response_model=list[ResearchTaskResponse])
async def list_research() -> list[ResearchTaskResponse]:
    return []


@router.get("/{task_id}", response_model=ResearchTaskResponse)
async def get_research(task_id: str) -> ResearchTaskResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=NOT_IMPLEMENTED
    )


@router.get(
    "/{task_id}/events",
    response_class=StreamingResponse,
    responses={200: {"content": {"text/event-stream": {}}}},
)
async def stream_research_events(task_id: str) -> StreamingResponse:
    return StreamingResponse(_empty_event_stream(), media_type="text/event-stream")


@router.get("/{task_id}/traces", response_model=list[AgentTraceResponse])
async def list_research_traces(task_id: str) -> list[AgentTraceResponse]:
    return []


@router.post("/{task_id}/cancel", response_model=CancelResponse)
async def cancel_research(task_id: str) -> CancelResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=NOT_IMPLEMENTED
    )
