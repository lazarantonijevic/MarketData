from datetime import UTC, datetime

import duckdb
from fastapi import APIRouter, Depends

from api.deps import get_meta_db
from api.schemas import HealthResponse

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Get the most recent pipeline run status",
)
def get_health(
    conn: duckdb.DuckDBPyConnection = Depends(get_meta_db),
):
    cursor = conn.execute("""
        SELECT
            run_id,
            started_at,
            finished_at,
            status,
            records_written,
            records_skipped,
            duration_seconds,
            error_message
        FROM pipeline_runs
        ORDER BY started_at DESC
        LIMIT 1
    """)

    columns = [desc[0] for desc in cursor.description]
    row = cursor.fetchone()

    if row is None:
        now = datetime.now(UTC)
        return {
            "run_id": "none",
            "started_at": now,
            "finished_at": now,
            "status": "failed",
            "records_written": 0,
            "records_skipped": 0,
            "duration_seconds": 0.0,
            "error_message": "no runs recorded",
        }

    return dict(zip(columns, row))
