from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


class CoinMarketRecord(BaseModel):
    """
    Single coin data record fetched from current market status
    """

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


class CoinHistoryRecord(BaseModel):
    """
    One hourly data point from historical data fetch
    """

    coin_id: str
    timestamp_ms: int
    price_usd: float = Field(gt=0, description="Price in USD")
    market_cap: float | None = None
    total_volume: float | None = None

    def to_market_record(self, symbol: str, name: str) -> CoinMarketRecord:
        """Promote to CoinMarketRecord"""
        return CoinMarketRecord(
            coin_id=self.coin_id,
            symbol=symbol,
            name=name,
            price_usd=self.price_usd,
            market_cap=self.market_cap,
            vol_24h=self.total_volume,
            price_change_24h_pct=None,
            high_24h=None,
            low_24h=None,
            ingested_at=datetime.fromtimestamp(self.timestamp_ms / 1000, tz=UTC),
        )
