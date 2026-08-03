with source as (
    select * from {{ ref('stg_prices') }}
)

select
    coin_id,
    date_day,

    -- OHLCV and market cap
    first(price_usd order by ingested_at)           as open,
    max(price_usd)                                  as high,
    min(price_usd)                                  as low,
    last(price_usd order by ingested_at)            as close,
    last(vol_24h order by ingested_at)              as total_volume,
    last(market_cap order by ingested_at)           as market_cap,

    -- passing columns for price summary mart
    last(price_change_24h_pct order by ingested_at) as price_change_24h_pct,
    last(symbol order by ingested_at)               as symbol,
    last(name order by ingested_at)                 as name,

    -- for diagnostics
    count(*)                                        as row_count
from source
group by coin_id, date_day
