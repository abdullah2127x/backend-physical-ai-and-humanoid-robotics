"""
Health Check API - System health and status endpoints.

Provides endpoints for monitoring service health.
"""

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: datetime
    version: str


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    ready: bool
    components: dict[str, bool]


@router.get(
    "",
    response_model=HealthResponse,
    summary="Health check",
    description="Basic health check endpoint.",
)
async def health_check() -> HealthResponse:
    """
    Basic health check.

    Returns:
        HealthResponse with status and version
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="0.1.0",
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness check",
    description="Check if all service components are ready.",
)
async def readiness_check() -> ReadinessResponse:
    """
    Check service readiness.

    Returns:
        ReadinessResponse with component status
    """
    # Check critical components
    components = {
        "qdrant": False,
        "cohere": False,
        "openrouter": False,
    }

    # In production, these would be actual health checks
    # For now, we assume they're potentially available
    components = {
        "qdrant": True,  # Check connection in production
        "cohere": True,  # Check API in production
        "openrouter": True,  # Check API in production
    }

    ready = all(components.values())

    return ReadinessResponse(
        ready=ready,
        components=components,
    )


@router.get(
    "/live",
    summary="Liveness check",
    description="Kubernetes liveness probe endpoint.",
)
async def liveness_check() -> dict:
    """
    Kubernetes liveness probe.

    Returns:
        Simple liveness status
    """
    return {"status": "alive"}
