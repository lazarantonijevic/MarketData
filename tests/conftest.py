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

    conn.execute("""
        CREATE TABLE mart_price_summary (
            coin_id                 VARCHAR,
            date_day                DATE,
            symbol                  VARCHAR,
            name                    VARCHAR,
            price_usd               DOUBLE,
            total_volume            DOUBLE,
            market_cap              DOUBLE,
            price_change_24h_pct    DOUBLE,
            ma_7d                   DOUBLE,
            ma_30d                  DOUBLE
        )
    """)

    conn.execute("""
        INSERT INTO mart_price_summary
        VALUES
        ('bitcoin', '2026-08-13', 'btc', 'Bitcoin', 65000.0,
         21000000000.0, 1273000000000.0, 2.5, 64000.0, 63000.0),
        ('ethereum', '2026-08-13', 'eth', 'Ethereum', 1900.0,
         6000000000.0, 226000000000.0, 3.5, 1850.0, 1850.0)
    """)

    return conn


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()
