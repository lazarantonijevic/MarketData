import duckdb
from fastapi import APIRouter, Depends, Query

from api.deps import get_db, verify_api_key
from api.schemas import AnomalyResponse

router = APIRouter(
    prefix="/anomalies",
    tags=["anomalies"],
    dependencies=[Depends(verify_api_key)],
)


@router.get(
    "/",
    response_model=list[AnomalyResponse],
    summary="Get all flagged volume anomalies",
)
def get_anomalies(
    severity: str | None = Query(default=None, pattern="^(high|medium)$"),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    conn: duckdb.DuckDBPyConnection = Depends(get_db),
):
    query = """
        SELECT
            coin_id,
            date_day,
            total_volume,
            avg_volume_30d,
            stddev_volume_30d,
            z_score,
            severity
        FROM mart_anomalies
        {}
        ORDER BY abs(z_score) DESC
        LIMIT ? OFFSET ?
    """

    if severity:
        cursor = conn.execute(
            query.format("WHERE severity = ?"), [severity, limit, offset]
        )
    else:
        cursor = conn.execute(query.format(""), [limit, offset])

    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    return [dict(zip(columns, row)) for row in rows]
