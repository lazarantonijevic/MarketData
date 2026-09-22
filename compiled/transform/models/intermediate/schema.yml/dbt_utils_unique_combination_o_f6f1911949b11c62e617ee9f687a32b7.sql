





with validation_errors as (

    select
        coin_id, date_day
    from "memory"."main"."int_ohlcv_daily"
    group by coin_id, date_day
    having count(*) > 1

)

select *
from validation_errors


