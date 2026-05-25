from datetime import datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from ingestion.models import CoinMarketRecord

MARKET_DATA_SCHEMA = pa.schema(
    [
        pa.field("coin_id", pa.string()),
        pa.field("symbol", pa.string()),
        pa.field("name", pa.string()),
        pa.field("price_usd", pa.float64()),
        pa.field("market_cap", pa.float64()),
        pa.field("vol_24h", pa.float64()),
        pa.field("price_change_24h_pct", pa.float64()),
        pa.field("high_24h", pa.float64()),
        pa.field("low_24h", pa.float64()),
        pa.field("ingested_at", pa.timestamp("us", tz="UTC")),
    ]
)


def write_market_data_batch(
    records: list[CoinMarketRecord],
    base_path: str,
    run_timestamp: datetime,
) -> Path:
    """Write a batch of validated records to a Parquet file.
    One file is writen per run, one parent directory per day.
    File path: {base_path}/date=YYYY-MM-DD/YYYY-MM-DDTHH-MM-SS.parquet
    """

    # Check for empty records list
    if not records:
        raise ValueError("Cannot write an empty records list.")

    # Convert Pydantic models to dicts
    rows = [r.model_dump() for r in records]
    # Convert to PyArrow table (columnar data)
    table = pa.Table.from_pylist(rows, schema=MARKET_DATA_SCHEMA)

    # Build partition directory
    date_str = run_timestamp.strftime("%Y-%m-%d")
    timestamp_str = run_timestamp.strftime("%Y-%m-%dT%H-%M-%S")
    out_dir = Path(base_path) / f"date={date_str}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write the file
    out_path = out_dir / f"{timestamp_str}.parquet"
    pq.write_table(table, out_path, compression="snappy")

    print(f"Wrote {len(records)} records to {out_path}")
    return out_path
