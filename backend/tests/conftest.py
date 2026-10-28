import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["TALENTFLOW_ENV"] = "test"

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed_enterprise_data  # noqa: E402
from app.services.bigquery_service import bq_warehouse  # noqa: E402


@pytest.fixture()
def test_db_session(tmp_path):
    db_file = tmp_path / "talentflow_test.sqlite"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as session:
        seed_enterprise_data(session)
        bq_warehouse.request_snapshots.clear()
        bq_warehouse.position_facts.clear()
        bq_warehouse.approval_events.clear()
        bq_warehouse.sync_run_count = 0
        yield session


@pytest.fixture()
def client(test_db_session):
    def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
