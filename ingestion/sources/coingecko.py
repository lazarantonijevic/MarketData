import asyncio
import json
import os

import httpx

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


if __name__ == "__main__":
    ids = asyncio.run(fetch_top_n_coin_ids(5))
    res = asyncio.run(fetch_current_market_data(ids))
    print(json.dumps(res, indent=2))
