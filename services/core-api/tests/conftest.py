import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core_api.db.base import Base
import core_api.db.models  # noqa: F401 — registra todos os modelos no metadata

TEST_DATABASE_URL = os.getenv(
    "CORE_TEST_DATABASE_URL",
    "postgresql+psycopg://helfy:helfy@localhost:5433/helfy_test",
)

engine = create_engine(TEST_DATABASE_URL)
TestingSession = sessionmaker(bind=engine, autoflush=False)


@pytest.fixture()
def db():
    with engine.connect() as conn:
        Base.metadata.drop_all(conn)
        Base.metadata.create_all(conn)
        conn.commit()
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        with engine.connect() as conn:
            Base.metadata.drop_all(conn)
            conn.commit()


@pytest.fixture()
def client(db):
    """TestClient com o banco de teste injetado no app."""
    from fastapi.testclient import TestClient

    from core_api.db.session import get_db
    from core_api.main import app

    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
