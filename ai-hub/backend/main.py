"""
AI Hub of Ideas & Tasks - Cloud Run entrypoint

This module creates the FastAPI application using the package `app`.
It avoids the naming collision with the `app` package when importing as a module.
"""
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from sqlalchemy import text

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine
from app.db.base import Base


# Setup structured logging
setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    logger.info("Starting AI Hub application")

    # Create database tables
    async with engine.begin() as conn:
        # Enable pgvector extension when running on Postgres (e.g., Supabase)
        try:
            if engine.url.get_backend_name().startswith("postgresql"):
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception:
            # Ignore if not supported or on non-Postgres backends
            pass
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created/verified")

    yield

    logger.info("Shutting down AI Hub application")


# Create FastAPI application
app = FastAPI(
    title="AI Hub of Ideas & Tasks",
    description="Centralized platform for collecting, routing, and managing user ideas with role-based workflows",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Include API routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ai-hub"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error("Unhandled exception", exc_info=exc, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_config=None,  # Use our custom logging
    )
