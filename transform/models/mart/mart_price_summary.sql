with ohlcv as (
    select
        coin_id,
        date_day,
        close,
        total_volume,
        market_cap,
        price_change_24h_pct,
        symbol,
        name
    from {{ ref('int_ohlcv_daily') }}
),

rolling as (
    select *
    from {{ ref('int_rolling_avg') }}
),

joined as (
    select
        rolling.coin_id,
        rolling.date_day,
        ohlcv.symbol,
        ohlcv.name,
        ohlcv.close                                 as price_usd,
        ohlcv.total_volume,
        ohlcv.market_cap,
        ohlcv.price_change_24h_pct,
        rolling.ma_7d,
        rolling.ma_30d
    from rolling
    inner join ohlcv
        on rolling.coin_id = ohlcv.coin_id
        and rolling.date_day = ohlcv.date_day
)

select * from joined
where date_day = (
    select max(date_day)
    from joined as j2
    where j2.coin_id = joined.coin_id
)