with source as (
    select * from {{ ref('int_ohlcv_daily') }}
)

select
    coin_id,
    date_day,

    -- rolling averages, 7-day and 30-day, current day included
    avg(close) over (
        partition by coin_id
        order by date_day
        range between interval '6 days' preceding and current row
    )                                               as ma_7d,
    avg(close) over (
        partition by coin_id
        order by date_day
        range between interval '29 days' preceding and current row
    )                                               as ma_30d
from source
