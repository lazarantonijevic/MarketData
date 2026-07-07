r"""
Backfill script that fetches historic hourly coin data from the past 89 days (or less).
The fetched data is validated, grouped by days and stored in Parquet files.
This script is intended for single use when starting up the project
and is not part of the scheduled flow.

script usage:
python -m ingestion.backfill --help
python -m ingestion.backfill --coins 50 --dry-run
python -m ingestion.backfill --coins 50 --days 89 --base-path data\sample\path
"""

import argparse
import asyncio
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import pyarrow.parquet as pq

from ingestion.models import CoinHistoryRecord
from ingestion.pipeline import DATA_RAW_PATH
from ingestion.sources.coingecko import fetch_coin_history
from ingestion.storage import write_market_data_batch
from ingestion.universe import load_universe


def check_partition_exists(base_path: Path, date_str: str, coin_id: str) -> bool:
    """
    Check if daily partition already exists for a coin to avoid writing dupicates
    """

    partition_dir = base_path / f"date={date_str}"
    if not partition_dir.exists():
        return False

    # Scan parquet files in the directory
    for file_path in partition_dir.glob("*.parquet"):
        try:
            table = pq.read_table(file_path, columns=["coin_id"])
            unique_coins = table.column("coin_id").to_pylist()
            if coin_id in unique_coins:
                return True
        except Exception:
            # skip unreadable files
            continue

    return False


async def backfill_coin(
    coin_id: str, symbol: str, name: str, days: int, base_path: Path
) -> int:
    """
    Fetch history, parse and write to Parquet the data for one coin
    Returns the number of written records
    """

    # Fetch from API
    try:
        history = await fetch_coin_history(coin_id, days=days)
    except Exception as e:
        print(f"Error fetching history for {coin_id}: {e}")
        return 0

    prices = history.get("prices", [])
    market_caps = history.get("market_caps", [])
    volumes = history.get("total_volumes", [])

    min_len = min(len(prices), len(market_caps), len(volumes))
    if min_len == 0:
        print(f"No history records found for {coin_id}.")
        return 0

    # Group records by date
    daily_records = defaultdict(list)
    skipped_count = 0

    for i in range(min_len):
        timestamp = prices[i][0]
        price = prices[i][1]
        cap = market_caps[i][1]
        vol = volumes[i][1]

        # ignore invalid prices
        if price <= 0:
            skipped_count += 1
            continue

        history_rec = CoinHistoryRecord(
            coin_id=coin_id,
            timestamp_ms=timestamp,
            price_usd=price,
            market_cap=cap,
            total_volume=vol,
        )

        market_rec = history_rec.to_market_record(symbol=symbol, name=name)
        record_date = market_rec.ingested_at.date()
        daily_records[record_date].append(market_rec)

    if skipped_count > 0:
        print(f"Skipped {skipped_count} invalid price points for {coin_id}")

    # Write daily batches
    num_written = 0
    for day, records in daily_records.items():
        date_str = day.strftime("%Y-%m-%d")

        # check for duplicates
        if check_partition_exists(
            base_path=base_path, date_str=date_str, coin_id=coin_id
        ):
            continue

        curr_time = datetime.now(UTC).time()
        run_timestamp = datetime.combine(day, curr_time, tzinfo=UTC)

        try:
            write_market_data_batch(
                records=records,
                base_path=str(base_path),
                run_timestamp=run_timestamp,
            )
            num_written += len(records)
        except Exception as e:
            print(f"Error writing batch for {coin_id} on {date_str}: {e}")

    return num_written


async def main():
    parser = argparse.ArgumentParser(description="Run historical backfill")
    parser.add_argument(
        "--coins",
        type=int,
        default=50,
        help="Number of coins from the universe to backfill",
    )
    parser.add_argument(
        "--days", type=int, default=89, help="Number of days to backfill (max 89)"
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default=DATA_RAW_PATH,
        help="Target folder for Parquet files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview run showing which coins would \
            be fetched and which partitions exist, \
            without making any API calls",
    )
    args = parser.parse_args()

    # Check for invalid number of days
    if args.days > 89:
        parser.error(
            "The --days argument cannot be greater\
                 than 89 due to CoinGecko's API limits."
        )

    # Load universe
    try:
        universe = load_universe()
    except Exception as e:
        print(e)
        return

    tracked_coins = universe[: args.coins]
    base_path = Path(args.base_path)

    # Dry-run mode
    if args.dry_run:
        print(
            f"[DRY RUN] Would backfill {len(tracked_coins)} coins over {args.days} days"
        )
        print(f"[DRY RUN] Output path: {base_path}")
        for indx, coin in enumerate(tracked_coins, 1):
            existing_days = sum(
                1
                for d in base_path.glob("date=*")
                if check_partition_exists(base_path, d.name.split("=")[1], coin["id"])
            )
            print(
                f"  {indx:3d}. {coin['id']:30s} ({existing_days} days already on disk)"
            )
        return

    print(f"Starting backfill for {len(tracked_coins)} coins over {args.days} days...")

    num_written = 0
    errors = 0
    start_time = time.monotonic()

    for index, coin in enumerate(tracked_coins, 1):
        coin_id = coin["id"]
        symbol = coin["symbol"]
        name = coin["name"]

        print(f"[{index}/{len(tracked_coins)}] Processing {coin_id}...")
        written = await backfill_coin(
            coin_id=coin_id,
            symbol=symbol,
            name=name,
            days=args.days,
            base_path=base_path,
        )

        if written > 0:
            num_written += written
        else:
            errors += 1
        print(f"[{index}/{len(tracked_coins)}] Wrote {written} records for {coin_id}")

        # Sleep 1 second between coins for API rate limiting purposes
        if index < len(tracked_coins):
            await asyncio.sleep(1.0)

    elapsed = time.monotonic() - start_time
    print(
        f"\nBackfill complete: {len(tracked_coins)} coins, "
        f"{num_written} records written, {errors} errors. "
        f"Duration: {elapsed:.1f}s"
    )


if __name__ == "__main__":
    asyncio.run(main())
