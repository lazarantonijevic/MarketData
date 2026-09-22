
    
    

select
    coin_id as unique_field,
    count(*) as n_records

from "memory"."main"."mart_price_summary"
where coin_id is not null
group by coin_id
having count(*) > 1


