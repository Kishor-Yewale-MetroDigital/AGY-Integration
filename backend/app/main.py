import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.seed import populate_interactive_approval_queue, seed_enterprise_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_enterprise_data(db)
        if os.getenv("AUTO_POPULATE_DEMO_QUEUE", "").lower() == "true":
            populate_interactive_approval_queue(db)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Enterprise Hiring Requisitions, Configurable People Committee Workflow, Workforce Planning & BigQuery Analytics",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


# NOTE: Cloud Run's Google Front End reserves "/healthz" (requests never reach the
# container), so "/health" is the path to use for checks against the deployed service.
@app.get("/health")
@app.get("/healthz", include_in_schema=False)
def healthcheck():
    return {
        "status": "ok",
        "service": "talentflow-backend",
        "environment": settings.environment,
        "bq_dataset": settings.bq_dataset,
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
