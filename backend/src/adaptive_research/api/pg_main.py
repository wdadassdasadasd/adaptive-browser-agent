"""P-01 PostgreSQL API process; long-running work belongs to the Worker."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from adaptive_research.api.pg_research import router as research_router
from adaptive_research.infrastructure.config import Settings, get_settings
from adaptive_research.infrastructure.pg_store import PgStore


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_async_engine(
            settings.require_postgres_url(), pool_pre_ping=True
        )
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
                await connection.execute(
                    text("SELECT id FROM scheduler_guard WHERE id = 1")
                )
            app.state.pg_store = PgStore(
                async_sessionmaker(engine, expire_on_commit=False)
            )
            yield
        finally:
            await engine.dispose()

    app = FastAPI(title="Adaptive Research Agent", version="0.2.0", lifespan=lifespan)
    app.state.settings = settings
    app.include_router(research_router)

    @app.exception_handler(SQLAlchemyError)
    async def database_unavailable(_request, _exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"detail": "Research database unavailable"},
            headers={"Retry-After": "2"},
        )

    app.add_exception_handler(OSError, database_unavailable)
    return app


app = create_app()
