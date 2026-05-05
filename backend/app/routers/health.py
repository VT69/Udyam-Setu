"""
Udyam Setu — Health Check Router
"""

from fastapi import APIRouter

from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> dict:
    """Return service health status."""
    return {"status": "ok", "service": "Udyam Setu"}
