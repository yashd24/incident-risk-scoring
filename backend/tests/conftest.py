"""API test fixtures.

Creates a temporary Postgres database for the test session, builds it with the Alembic
migrations, seeds it, and drops it at the end. The server is TEST_DATABASE_URL (any
database name on it works, it is only used to connect and create/drop the temporary
one). The default matches the compose database on host port 5433. See README "Run tests".
"""

import os
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.db import get_db
from app.main import app
from app.seed import seed

BACKEND = Path(__file__).resolve().parent.parent
SERVER_URL = make_url(
    os.environ.get("TEST_DATABASE_URL", "postgresql+psycopg2://risk:risk@127.0.0.1:5433/postgres")
)


@pytest.fixture(scope="session")
def engine():
    name = f"risk_test_{uuid.uuid4().hex[:8]}"
    admin = create_engine(SERVER_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{name}"'))
    test_url = SERVER_URL.set(database=name)
    try:
        cfg = Config(str(BACKEND / "alembic.ini"))
        cfg.set_main_option("script_location", str(BACKEND / "alembic"))
        cfg.set_main_option(
            "sqlalchemy.url", test_url.render_as_string(hide_password=False).replace("%", "%%")
        )
        command.upgrade(cfg, "head")
        eng = create_engine(test_url)
        yield eng
        eng.dispose()
    finally:
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        admin.dispose()


@pytest.fixture()
def client(engine):
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with engine.begin() as conn:  # fresh state per test; alerts are reseeded below
        conn.execute(text("TRUNCATE alerts, cases RESTART IDENTITY CASCADE"))
    with Session() as s:
        seed(s)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
