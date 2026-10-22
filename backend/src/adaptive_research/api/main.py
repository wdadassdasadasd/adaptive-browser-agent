"""FastAPI application entry point and resource lifespan."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from adaptive_research.api.research import router as research_router
from adaptive_research.application.research import ResearchService
from adaptive_research.infrastructure.config import Settings, get_settings
from adaptive_research.infrastructure.db.session import initialize_schema


def create_app(settings: Settings | None = None, agent_factory=None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_async_engine(settings.database_url)
        try:
            await initialize_schema(engine)
            sessions = async_sessionmaker(engine, expire_on_commit=False)
            service = ResearchService(settings, sessions, agent_factory)
            app.state.research = service
            await service.recover()
            try:
                yield
            finally:
                await service.shutdown()
        finally:
            await engine.dispose()

    app = FastAPI(title="Adaptive Browser Agent", version="0.1.0", lifespan=lifespan)
    app.include_router(research_router)
    return app


app = create_app()
