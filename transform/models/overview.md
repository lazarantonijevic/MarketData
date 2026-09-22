{% docs __overview__ %}
# Cryptocurrency Market Data Platform

An end-to-end data engineering pipeline that ingests live and historical cryptocurrency market data, transforms it through a layered dbt model structure and serves it via a REST API and a dashboard.

## Architecture

- **Ingestion** - CoinGecko REST API, Python, Pydantic validation, Parquet storage
- **Orchestration** - Prefect, self-hosted, 15-minute scheduled runs
- **Transformation** - DuckDB + dbt
- **Serving** - FastAPI, read-only DuckDB access
- **Dashboard** - Streamlit with a live Binance WebSocket ticker

## Model layers

| Layer | Purpose |
|---|---|
| `staging` | Cleans and casts raw ingested data, one model per source |
| `intermediate` | OHLCV aggregation, rolling averages, volume Z-scores |
| `mart` | Final tables served by the API — price summary, OHLCV, anomalies |

## Useful starting points

- [`mart_price_summary`](#!/model/model.crypto_platform.mart_price_summary) — current price and moving averages per coin
- [`mart_ohlcv`](#!/model/model.crypto_platform.mart_ohlcv) — daily OHLCV candles
- [`mart_anomalies`](#!/model/model.crypto_platform.mart_anomalies) — flagged volume anomalies

Source: [GitHub repository](https://github.com/<your-username>/<repo-name>)

{% enddocs %}