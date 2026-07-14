with source as (
    {% if target.name == 'ci' %}
        select * from {{ ref('raw_prices_sample') }}
    {% else %}
        select * from {{ source('raw', 'raw_prices') }}
    {% endif %}
),

cleaned as (
    select
        coin_id::varchar                            as coin_id,
        symbol::varchar                             as symbol,
        name::varchar                               as name,
        price_usd::double                           as price_usd,
        market_cap::double                          as market_cap,
        vol_24h::double                             as vol_24h,
        price_change_24h_pct::double                as price_change_24h_pct,
        high_24h::double                            as high_24h,
        low_24h::double                             as low_24h,
        ingested_at::timestamptz                    as ingested_at,
        date_trunc('day', ingested_at::timestamptz) as date_day
    from source
    where price_usd > 0
        and price_usd is not null
        and coin_id is not null
)

select * from cleaned