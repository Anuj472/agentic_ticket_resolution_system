import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import (
    TicketNotFoundError,
    DuplicateTicketError,
    ticket_not_found_handler,
    duplicate_ticket_handler,
)
from app.core.redis import close_redis

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle events."""
    logger.info("[APP] Starting Agentic Ticket System")
    yield
    logger.info("[APP] Shutting down — closing Redis connection")
    await close_redis()


app = FastAPI(
    title="Agentic Ticket System",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── CORS — use configured origins, NOT wildcard ─────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")

# ── Custom exception handlers ────────────────────────────────────────────────
app.add_exception_handler(TicketNotFoundError, ticket_not_found_handler)
app.add_exception_handler(DuplicateTicketError, duplicate_ticket_handler)

# ── Prometheus metrics ───────────────────────────────────────────────────────
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/")
async def root():
    return {"status": "ok", "docs": "/api/docs"}
