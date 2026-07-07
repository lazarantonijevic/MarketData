import asyncio
from datetime import UTC, datetime

from pydantic import ValidationError

from ingestion.models import CoinMarketRecord
from ingestion.sources.coingecko import fetch_current_market_data
from ingestion.storage import write_market_data_batch
from ingestion.universe import load_universe

DATA_RAW_PATH = "data/raw/prices"


async def run_pipeline(num_coins: int = 50) -> None:
    """Fetch market data for preset list of coins,
    validate via Pydantic, and write to Parquet."""

    coin_ids = [coin["id"] for coin in load_universe()]
    raw_data = await fetch_current_market_data(coin_ids)

    # Validate rows using Pydantic model
    records: list[CoinMarketRecord] = []
    for item in raw_data:
        try:
            record = CoinMarketRecord(
                coin_id=item.get("id"),
                symbol=item.get("symbol"),
                name=item.get("name"),
                price_usd=item.get("current_price"),
                market_cap=item.get("market_cap"),
                vol_24h=item.get("total_volume"),
                price_change_24h_pct=item.get("price_change_percentage_24h"),
                high_24h=item.get("high_24h"),
                low_24h=item.get("low_24h"),
                ingested_at=datetime.now(UTC),
            )
            records.append(record)
        except ValidationError as e:
            # Skip invalid records
            print(f"Skipping {item.get('id', 'unknown')}: {e}")

    print(f"Validated {len(records)}/{len(raw_data)} records.")

    # Write records to Parquet
    write_market_data_batch(records, DATA_RAW_PATH, run_timestamp=datetime.now(UTC))


if __name__ == "__main__":
    asyncio.run(run_pipeline(num_coins=10))
