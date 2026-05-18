from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


class CoinMarketRecord(BaseModel):
    coin_id: str
    symbol: str
    name: str
    price_usd: float = Field(gt=0, description="Price in USD")
    market_cap: float | None = None
    vol_24h: float | None = None
    price_change_24h_pct: float | None = None
    high_24h: float | None = None
    low_24h: float | None = None
    ingested_at: datetime

    @field_validator("coin_id", "symbol")
    def must_be_lowercase(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("ingested_at")
    def check_not_in_future(cls, v: datetime) -> datetime:
        if v > datetime.now(UTC):
            raise ValueError("ingested_at cannot be in the future")
        return v
