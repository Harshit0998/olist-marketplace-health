-- One row per lateness band. This is the dose-response chart.
-- Bands match docs/findings.md exactly. band_order exists so Power BI sorts by
-- severity rather than alphabetically, which would put '15+ days late' first.

with orders as (
    select
        case when delay_days <=  0 then 'On time'
             when delay_days <=  3 then '1-3 days late'
             when delay_days <=  7 then '4-7 days late'
             when delay_days <= 14 then '8-14 days late'
             else                       '15+ days late'
        end as delay_band,
        case when delay_days <=  0 then 0
             when delay_days <=  3 then 1
             when delay_days <=  7 then 2
             when delay_days <= 14 then 3
             else                       4
        end as band_order,
        review_score
    from {{ ref('fct_orders') }}
    where is_late is not null
)

select
    band_order,
    delay_band,
    count(*)                                        as n_orders,
    count(review_score)                             as n_reviews,
    sum(review_score)                               as review_points,
    count(*) filter (where review_score <= 2)       as n_low,
    avg(review_score)                               as avg_review,
    count(*) filter (where review_score <= 2) * 1.0
      / nullif(count(review_score), 0)              as low_review_rate
from orders
group by band_order, delay_band
order by band_order
