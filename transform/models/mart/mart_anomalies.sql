with source as (
    select * from {{ ref('int_volume_zscore') }}
)

select
    coin_id,
    date_day,
    total_volume,
    avg_volume_30d,
    stddev_volume_30d,
    z_score,
    case
        when abs(z_score) > 3.0 then 'high'
        else 'medium'
    end                                                 as severity
from source
where abs(z_score) > 2.5
