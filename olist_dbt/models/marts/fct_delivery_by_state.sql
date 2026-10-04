-- One row per customer state. Feeds the delivery map on the dashboard.
--
-- Restricted to orders where lateness is KNOWN, so every rate here shares the
-- same denominator as the headline late rate in docs/findings.md. This is the
-- customer's state (where the parcel went), not the seller's.
--
-- state_name and region come from the br_states seed: reference data that is not
-- in the Olist export at all, so it lives in the repo as a CSV rather than being
-- hardcoded into a CASE expression.

with orders as (
    select o.order_id,
           c.state,
           o.is_late,
           o.review_score,
           o.delivery_days
    from {{ ref('fct_orders') }} o
    join {{ ref('stg_customers') }} c on c.customer_id = o.customer_id
    where o.is_late is not null
),

by_state as (
    select
        state,
        count(*)                                            as n_orders,
        count(*) filter (where is_late)                     as n_late,
        count(*) * 1.0 / sum(count(*)) over ()              as share_of_orders,
        count(*) filter (where is_late) * 1.0 / count(*)    as late_rate,

        avg(review_score) filter (where not is_late)        as review_ontime,
        avg(review_score) filter (where     is_late)        as review_late,
        avg(review_score) filter (where not is_late)
          - avg(review_score) filter (where is_late)        as review_gap,

        count(*) filter (where not is_late and review_score <= 2) * 1.0
          / nullif(count(review_score) filter (where not is_late), 0) as low_review_rate_ontime,
        count(*) filter (where     is_late and review_score <= 2) * 1.0
          / nullif(count(review_score) filter (where     is_late), 0) as low_review_rate_late,

        avg(delivery_days)                                  as avg_delivery_days
    from orders
    group by state
)

select
    b.state,
    s.state_name,
    s.region,
    b.n_orders,
    b.n_late,
    b.share_of_orders,
    b.late_rate,
    b.review_ontime,
    b.review_late,
    b.review_gap,
    b.low_review_rate_ontime,
    b.low_review_rate_late,
    b.avg_delivery_days
from by_state b
left join {{ ref('br_states') }} s on s.state = b.state
order by b.late_rate desc
