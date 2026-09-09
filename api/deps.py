import os
import secrets

import duckdb
from dotenv import load_dotenv
from fastapi import Header, HTTPException, status

load_dotenv()


def get_db():
    conn = duckdb.connect(os.environ["DUCKDB_WAREHOUSE_PATH"], read_only=True)
    conn.execute("SET TimeZone='UTC'")
    try:
        yield conn
    finally:
        conn.close()


def get_meta_db():
    conn = duckdb.connect(os.environ["DUCKDB_META_PATH"], read_only=True)
    conn.execute("SET TimeZone='UTC'")
    try:
        yield conn
    finally:
        conn.close()


def verify_api_key(x_api_key: str = Header(...)) -> None:
    if not secrets.compare_digest(x_api_key, os.environ["API_KEY"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )
