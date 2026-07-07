"""
Sets a static list of coins that will be tracked in order to
prevent issues with coins fluctuating in and out of the top N.
ID, symbol and name of the coins are stored in a json file.
Executable from command line with arguments

universe format:
[
  {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
  {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
  ...
]

script usage:
python -m ingestion.universe --help
python -m ingestion.universe --init --coins 50
python -m ingestion.universe --list
"""

import argparse
import json
from pathlib import Path

from ingestion.sources.coingecko import fetch_top_n_coins

UNIVERSE_FILE_PATH = Path("data/meta/universe.json")


async def initialize_universe(top_n: int = 50) -> Path:
    """
    Fetch top_n coins from the API
    Save them to universe.json
    Return path to file
    Raise FileExistsError if file already exists
    """

    if UNIVERSE_FILE_PATH.exists():
        raise FileExistsError(
            f"Universe file already exists at {UNIVERSE_FILE_PATH}. "
            "Delete it manually to re-initialize."
        )

    coins = await fetch_top_n_coins(top_n)

    UNIVERSE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    UNIVERSE_FILE_PATH.write_text(json.dumps(coins, indent=2), encoding="utf-8")

    print(f"Initialized universe with {len(coins)} coins to {UNIVERSE_FILE_PATH}")
    return UNIVERSE_FILE_PATH


def load_universe() -> list[dict]:
    """
    Load coins from the json file
    Return coin IDs, symbols and names as list of dicts
    Raise FileNotFoundError if file is missing
    """

    if not UNIVERSE_FILE_PATH.exists():
        raise FileNotFoundError(
            f"Universe file not found at {UNIVERSE_FILE_PATH}. "
            "Initiate the universe first."
        )
    return json.loads(UNIVERSE_FILE_PATH.read_text(encoding="utf-8"))


def get_coin(universe: list[dict], coin_id: str) -> dict:
    """
    Fetch a coin from the universe based on the ID
    Raise KeyError if coin not found
    """

    for coin in universe:
        if coin["id"] == coin_id:
            return coin

    raise KeyError(f"Coin '{coin_id}' not found in the list")


if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="Manage coin universe")

    parser.add_argument("--init", action="store_true", help="Initialize universe.json")
    parser.add_argument(
        "--coins", type=int, default=50, help="Number of top coins (default 50)"
    )
    parser.add_argument("--list", action="store_true", help="Print current universe")

    args = parser.parse_args()

    if args.init:
        asyncio.run(initialize_universe(top_n=args.coins))
    elif args.list:
        coins = load_universe()
        for i, c in enumerate(coins, 1):
            print(f"  {i:3d}. {c['id']:30s} {c['symbol']:8s} {c['name']}")
    else:
        parser.print_help()
