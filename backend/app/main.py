from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from prometheus_fastapi_instrumentator import Instrumentator
app = FastAPI(
    title="Agentic Ticket System",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api/v1")

# Initialize Prometheus instrumentation
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
@app.get("/")
async def root():
    return {"status": "ok", "docs": "/api/docs"}
