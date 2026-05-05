"""
Udyam Setu — FastAPI Application Entry Point
Business Identity Resolution System
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import health, entities, entity_resolution, events, activity


# ── Lifespan ──────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup (dev convenience); use Alembic in prod."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


# ── App factory ───────────────────────────────────────────────
app = FastAPI(
    title="Udyam Setu",
    description=(
        "Business Identity Resolution System — "
        "linking fragmented MSME identities across Indian regulatory databases."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS (allow all origins in development) ───────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────
app.include_router(health.router, tags=["Health"])
app.include_router(entities.router, prefix="/api/v1", tags=["Entities"])
app.include_router(entity_resolution.router, prefix="/api/er", tags=["Entity Resolution"])
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(activity.router, prefix="/api", tags=["Activity Intelligence"])
