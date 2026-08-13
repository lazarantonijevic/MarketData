import duckdb
from fastapi import APIRouter, Depends, HTTPException, status

from api.deps import get_db, verify_api_key
from api.schemas import PriceSummaryResponse

router = APIRouter(
    prefix="/prices",
    tags=["prices"],
    dependencies=[Depends(verify_api_key)],
)


COLUMNS = [
    "coin_id",
    "date_day",
    "symbol",
    "name",
    "price_usd",
    "total_volume",
    "market_cap",
    "price_change_24h_pct",
    "ma_7d",
    "ma_30d",
]


@router.get(
    "/",
    response_model=list[PriceSummaryResponse],
    summary="Get current price summary for all coins",
)
def get_all_prices(conn: duckdb.DuckDBPyConnection = Depends(get_db)):
    rows = conn.execute("""
        SELECT
            coin_id,
            date_day,
            symbol,
            name,
            price_usd,
            total_volume,
            market_cap,
            price_change_24h_pct,
            ma_7d,
            ma_30d
        FROM mart_price_summary
        ORDER BY market_cap DESC NULLS LAST
    """).fetchall()

    return [dict(zip(COLUMNS, row)) for row in rows]


@router.get(
    "/{coin_id}",
    response_model=PriceSummaryResponse,
    summary="Get current price summary for a single coin",
)
def get_price(coin_id: str, conn: duckdb.DuckDBPyConnection = Depends(get_db)):
    row = conn.execute(
        """
        SELECT
            coin_id,
            date_day,
            symbol,
            name,
            price_usd,
            total_volume,
            market_cap,
            price_change_24h_pct,
            ma_7d,
            ma_30d
        FROM mart_price_summary
        WHERE coin_id = ?
    """,
        [coin_id.lower()],
    ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Coin '{coin_id}' not found"
        )

    return dict(zip(COLUMNS, row))
