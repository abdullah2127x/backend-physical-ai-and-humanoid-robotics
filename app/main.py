"""
FastAPI Application Factory - Create and configure the ASGI application.

Provides the main FastAPI app instance with middleware and route registration.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import get_settings
from src.core.vector import get_qdrant, init_qdrant

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager - startup and shutdown events."""
    settings = get_settings()

    logger.info("Starting RAG Chatbot Backend", version="0.1.0")

    # Initialize Qdrant connection
    try:
        await init_qdrant()
        logger.info("Qdrant connection established")
    except Exception as e:
        logger.warning("Failed to connect to Qdrant - running in degraded mode", error=str(e))

    yield

    # Shutdown
    logger.info("Shutting down RAG Chatbot Backend")
    qdrant = get_qdrant()
    await qdrant.disconnect()


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI app instance
    """
    settings = get_settings()

    app = FastAPI(
        title="RAG Chatbot API",
        description="Backend API for RAG-powered book content Q&A",
        version="0.1.0",
        lifespan=lifespan,
        debug=settings.app_debug,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    # Register routes
    from src.api.chat import router as chat_router
    from src.api.health import router as health_router

    app.include_router(health_router, prefix="/health", tags=["Health"])
    app.include_router(chat_router, prefix="/chat", tags=["Chat"])

    logger.info("FastAPI application created", debug=settings.app_debug)

    return app


# Create app instance
app = create_app()


def main():
    """Run the application with uvicorn."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )


if __name__ == "__main__":
    main()
