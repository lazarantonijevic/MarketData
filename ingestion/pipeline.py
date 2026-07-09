from datetime import UTC, datetime
from uuid import uuid4

from prefect import flow, task
from pydantic import ValidationError

from ingestion.models import CoinMarketRecord, PipelineRun
from ingestion.sources.coingecko import fetch_current_market_data
from ingestion.storage import log_pipeline_run, write_market_data_batch
from ingestion.universe import load_universe

DATA_RAW_PATH = "data/raw/prices"


async def run_pipeline() -> tuple[int, int]:
    """Fetch market data for preset list of coins,
    validate via Pydantic, and write to Parquet."""

    coin_ids = [coin["id"] for coin in load_universe()]
    raw_data = await fetch_current_market_data(coin_ids)

    # Validate rows using Pydantic model
    records: list[CoinMarketRecord] = []
    skipped = 0
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
            skipped += 1
            print(f"Skipping {item.get('id', 'unknown')}: {e}")

    print(f"Validated {len(records)}/{len(raw_data)} records.")

    # Write records to Parquet
    write_market_data_batch(records, DATA_RAW_PATH, run_timestamp=datetime.now(UTC))
    return len(records), skipped


@task(name="run-pipeline")
async def pipeline_task() -> tuple[int, int]:
    """
    Prefect task wrapper around run_pipeline().
    Implemented separately to allow run_pipeline() to be executed outside
    of Prefect for testing purposes.
    """
    return await run_pipeline()


@flow(name="crypto-ingestion", log_prints=True)
async def ingest_flow() -> None:
    """
    Orchestrated flow
    - Runs the pipeline
    - Logs run metadata to DuckDB
    """

    run_id = str(uuid4())
    started_at = datetime.now(UTC)

    try:
        written, skipped = await pipeline_task()
        status = "success"
        error_message = None
    except Exception as e:
        written, skipped = 0, 0
        status = "failed"
        error_message = str(e)

    finished_at = datetime.now(UTC)
    log_pipeline_run(
        run=PipelineRun(
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            status=status,
            records_written=written,
            records_skipped=skipped,
            duration_seconds=(finished_at - started_at).total_seconds(),
            error_message=error_message,
        )
    )


if __name__ == "__main__":
    # Schedule Prefect flow to run every 15 minutes
    ingest_flow.serve(name="crypto-ingest-15m", interval=900)
