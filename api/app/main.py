"""FastAPI application entry point for the E-Commerce API.

Defines `app` and a simple health endpoint used by tests and other components.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.app.db import init_db
from api.app.routers import auth


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Create database tables on startup."""
    init_db()
    yield


app = FastAPI(title="E-Commerce API", lifespan=lifespan)
app.include_router(auth.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint.

    Returns a tiny JSON object used by tests and orchestration systems.

    Returns:
        A mapping with a single key "status" and value "ok".
    """
    return {"status": "ok"}
