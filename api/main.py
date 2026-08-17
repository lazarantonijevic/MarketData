from fastapi import FastAPI

from api.routers import anomalies, ohlcv, prices

app = FastAPI(
    title="MarketData",
    description=(
        "REST API serving cryptocurrency market data, "
        "OHLCV candles, and volume anomalies."
    ),
    version="1.0.0",
)


app.include_router(prices.router)
app.include_router(ohlcv.router)
app.include_router(anomalies.router)


@app.get("/")
def root():
    return {"status": "ok"}
