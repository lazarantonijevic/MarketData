with source as (
    select * from {{ ref('int_ohlcv_daily') }}
)

select
    coin_id,
    symbol,
    name,
    date_day,
    open,
    high,
    low,
    close,
    total_volume,
    market_cap,
    row_count
from source