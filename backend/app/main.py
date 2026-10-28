from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.seed import seed_enterprise_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_enterprise_data(db)
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


@app.get("/healthz")
def healthcheck():
    return {
        "status": "ok",
        "service": "talentflow-backend",
        "environment": settings.environment,
        "bq_dataset": settings.bq_dataset,
    }


frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
