import duckdb
from fastapi import APIRouter, Depends, HTTPException, status

from api.deps import get_db, verify_api_key
from api.schemas import OHLCVResponse

router = APIRouter(
    prefix="/ohlcv",
    tags=["ohlcv"],
    dependencies=[Depends(verify_api_key)],
)


COLUMNS = [
    "coin_id",
    "symbol",
    "name",
    "date_day",
    "open",
    "high",
    "low",
    "close",
    "total_volume",
    "market_cap",
    "row_count",
]


@router.get(
    "/{coin_id}",
    response_model=list[OHLCVResponse],
    summary="Get full OHLCV time series for a coin",
)
def get_ohlcv(
    coin_id: str,
    conn: duckdb.DuckDBPyConnection = Depends(get_db),
):
    rows = conn.execute(
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
    ).fetchall()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Coin '{coin_id}' not found"
        )

    return [dict(zip(COLUMNS, row)) for row in rows]
