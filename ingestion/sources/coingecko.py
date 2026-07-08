import asyncio
import json
import os

import httpx
from dotenv import load_dotenv

load_dotenv()
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
BASE_URL = "https://api.coingecko.com/api/v3"


# Get needed header for API authentication
def get_header() -> dict:
    if not COINGECKO_API_KEY:
        return {}
    return {"x-cg-demo-api-key": COINGECKO_API_KEY}


# Fetch top n coin IDs (by market cap)
async def fetch_top_n_coin_ids(n: int) -> list[str]:
    url = f"{BASE_URL}/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": str(n),
        "page": "1",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=get_header())
        response.raise_for_status()
        data = response.json()

        return [coin["id"] for coin in data]


# Fetch IDs, symbols and names of top n coins (by market cap)
async def fetch_top_n_coins(n: int) -> list[dict]:
    url = f"{BASE_URL}/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": str(n),
        "page": "1",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=get_header())
        response.raise_for_status()
        data = response.json()

        return [
            {"id": coin["id"], "symbol": coin["symbol"], "name": coin["name"]}
            for coin in data
        ]


# Fetch current market data for a list of coins
async def fetch_current_market_data(coin_ids: list[str]) -> list[dict]:
    url = f"{BASE_URL}/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(coin_ids),
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=get_header())
        response.raise_for_status()
        return response.json()


# Fetch historical market data for a single coin
async def fetch_coin_history(
    coin_id: str, vs_currency: str = "usd", days: int = 89
) -> dict:
    """
    Returns data in format:
    {
    "prices": [[timestamp,price], ...],
    "market_caps": [[timestamp, mc], ...],
    "total_volumes": [[timestamp, vol], ...]
    }
    """
    if days > 89:
        raise ValueError(
            f"days parameter ({days}) must be 89 or less."
            "Coingecko only returns hourly data points for intervals < 90 days."
        )

    url = f"{BASE_URL}/coins/{coin_id}/market_chart"
    params = {"vs_currency": vs_currency, "days": str(days)}

    async with httpx.AsyncClient() as client:
        response = await client.get(url=url, params=params, headers=get_header())
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    ids = asyncio.run(fetch_top_n_coin_ids(5))
    res = asyncio.run(fetch_current_market_data(ids))
    print(json.dumps(res, indent=2))
