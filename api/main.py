from fastapi import FastAPI

app = FastAPI(
    title="MarketData",
    description=(
        "REST API serving cryptocurrency market data, "
        "OHLCV candles, and volume anomalies."
    ),
    version="1.0.0",
)


@app.get("/")
def root():
    return {"status": "ok"}
