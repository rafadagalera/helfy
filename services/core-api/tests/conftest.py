import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core_api.db.base import Base

TEST_DATABASE_URL = "postgresql+psycopg://helfy:helfy@localhost:5433/helfy_test"

engine = create_engine(TEST_DATABASE_URL)
TestingSession = sessionmaker(bind=engine, autoflush=False)


@pytest.fixture()
def db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


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
