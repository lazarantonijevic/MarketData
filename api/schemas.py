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
