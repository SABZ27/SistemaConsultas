import os

os.environ["DB_URL"] = "sqlite+pysqlite:///./test_bd.sqlite3"

import pytest
from fastapi.testclient import TestClient

from app.db.session import engine
from app.main import app
from app.models import Base


@pytest.fixture(scope="session", autouse=True)
def _esquema():
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    if os.path.exists("test_bd.sqlite3"):
        os.remove("test_bd.sqlite3")


@pytest.fixture(autouse=True)
def _limpiar_bd(_esquema):
    with engine.begin() as conn:
        for tabla in reversed(Base.metadata.sorted_tables):
            conn.execute(tabla.delete())
    yield


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c