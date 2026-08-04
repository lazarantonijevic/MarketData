with source as (
    select * from {{ ref('int_ohlcv_daily') }}
),

windowed as (
    select
        coin_id,
        date_day,
        total_volume,

        avg(total_volume) over (
            partition by coin_id
            order by date_day
            range between interval '29 days' preceding and current row
        )                                               as avg_volume_30d,

        stddev_pop(total_volume) over (
            partition by coin_id
            order by date_day
            range between interval '29 days' preceding and current row
        )                                               as stddev_volume_30d
    from source
    where total_volume is not null
)

select
    coin_id,
    date_day,
    total_volume,
    avg_volume_30d,
    stddev_volume_30d,

    case
        when stddev_volume_30d = 0 or stddev_volume_30d is null
        then null
        else (total_volume - avg_volume_30d) / stddev_volume_30d
    end                                             as z_score
from windowed
