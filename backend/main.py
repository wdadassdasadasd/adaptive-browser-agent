"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.research import router as research_router
from backend.db.session import dispose_engine, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    try:
        yield
    finally:
        await dispose_engine()


app = FastAPI(title="Adaptive Browser Agent", version="0.1.0", lifespan=lifespan)
app.include_router(research_router)
