from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    tickets,
    users,
    stream,
    analytics,
    evaluation,
    ingest,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(stream.router, tags=["Stream"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(evaluation.router, tags=["Evaluation"])
