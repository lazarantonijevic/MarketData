from datetime import date

from pydantic import BaseModel


class PriceSummaryResponse(BaseModel):
    coin_id: str
    date_day: date
    symbol: str
    name: str
    price_usd: float
    total_volume: float
    market_cap: float
    price_change_24h_pct: float | None = None
    ma_7d: float
    ma_30d: float


class OHLCVResponse(BaseModel):
    coin_id: str
    symbol: str
    name: str
    date_day: date
    open: float
    high: float
    low: float
    close: float
    total_volume: float
    market_cap: float
    row_count: int


class AnomalyResponse(BaseModel):
    coin_id: str
    date_day: date
    total_volume: float
    avg_volume_30d: float
    stddev_volume_30d: float
    z_score: float
    severity: str
