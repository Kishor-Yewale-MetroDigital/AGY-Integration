import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TalentFlow — Enterprise Hiring & People Committee Platform"
    environment: str = os.getenv("TALENTFLOW_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./talentflow.db")
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "cf-hackathon-ai-poc-testin-b1")
    bq_dataset: str = os.getenv("BQ_DATASET", "talentflow_analytics")
    default_sla_hours: int = 48
    fiscal_year: int = 2026

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
