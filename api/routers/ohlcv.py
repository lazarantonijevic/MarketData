import duckdb
from fastapi import APIRouter, Depends, HTTPException, status

from api.deps import get_db, verify_api_key
from api.schemas import OHLCVResponse

router = APIRouter(
    prefix="/ohlcv",
    tags=["ohlcv"],
    dependencies=[Depends(verify_api_key)],
)


@router.get(
    "/{coin_id}",
    response_model=list[OHLCVResponse],
    summary="Get full OHLCV time series for a coin",
)
def get_ohlcv(
    coin_id: str,
    conn: duckdb.DuckDBPyConnection = Depends(get_db),
):
    cursor = conn.execute(
        """
        SELECT
            coin_id,
            symbol,
            name,
            date_day,
            open,
            high,
            low,
            close,
            total_volume,
            market_cap,
            row_count
        FROM mart_ohlcv
        WHERE coin_id = ?
        ORDER BY date_day ASC
    """,
        [coin_id.lower()],
    )

    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Coin '{coin_id}' not found"
        )

    return [dict(zip(columns, row)) for row in rows]
