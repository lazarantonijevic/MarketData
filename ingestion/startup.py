import asyncio
import os
import subprocess
import sys

from ingestion.universe import initialize_universe

NUM_COINS = os.environ.get("NUM_COINS", "50")
BACKFILL_DAYS = os.environ.get("BACKFILL_DAYS", "89")


async def ensure_universe() -> None:
    try:
        await initialize_universe(top_n=int(NUM_COINS))
    except FileExistsError:
        print("Universe already initialized, skipping.")


def run_backfill() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "ingestion.backfill",
            "--days",
            BACKFILL_DAYS,
            "--coins",
            NUM_COINS,
        ],
        check=True,
    )


if __name__ == "__main__":
    asyncio.run(ensure_universe())
    run_backfill()
