import asyncio
import json

import httpx


# Sample data fetch from CoinGecko and print in console
async def fetch_sample_data() -> None:
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": "5",
        "page": "1",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        print("RAW JSON:")
        print(json.dumps(data, indent=2))


# Fetch top n coin IDs (by market cap)
async def fetch_top_n_coin_ids(n: int) -> list[str]:
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": str(n),
        "page": "1",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        return [coin["id"] for coin in data]


# Fetch current market data for a list of coins
async def fetch_current_market_data(coin_ids: list[str]) -> list[dict]:
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(coin_ids),
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    # asyncio.run(fetch_sample_data())
    ids = asyncio.run(fetch_top_n_coin_ids(5))
    res = asyncio.run(fetch_current_market_data(ids))
    print(json.dumps(res, indent=2))
