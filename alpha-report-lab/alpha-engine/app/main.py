"""FastAPI entry point for the Alpha Engine.

CRITICAL: setup_instrumentation() must run BEFORE the OpenAI client is created
so that OpenInference can monkey-patch openai.
"""
from __future__ import annotations

import logging
import os

# --- Instrumentation must come first ---
from app.instrumentation import setup_instrumentation, shutdown as shutdown_tracing

setup_instrumentation()

# --- Now safe to import the rest ---
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import alpha, embeddings, health
from app.services.context import ContextManager
from app.services.report_store import ReportStore

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("alpha-engine")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.report_store = ReportStore()
    app.state.context_mgr = ContextManager()
    logger.info(f"Alpha Engine starting on port {settings.PORT}")
    try:
        yield
    finally:
        logger.info("Shutting down tracing...")
        shutdown_tracing()


app = FastAPI(title="Alpha Engine", version=settings.SERVICE_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logger(request: Request, call_next):
    logger.info(f"--> {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"<-- {request.method} {request.url.path} [{response.status_code}]")
    return response


app.include_router(health.router)
app.include_router(alpha.router)
app.include_router(embeddings.router)


@app.get("/")
async def root():
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "docs": "/docs",
    }
