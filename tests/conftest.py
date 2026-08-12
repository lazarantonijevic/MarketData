import os

os.environ.setdefault("API_KEY", "test-key-for-pytest")
os.environ.setdefault("DUCKDB_WAREHOUSE_PATH", ":memory:")

import duckdb
import pytest
from fastapi.testclient import TestClient

from api.deps import get_db
from api.main import app


@pytest.fixture
def db():
    conn = duckdb.connect(":memory:")
    conn.execute("SET TimeZone='UTC'")
    return conn


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()
