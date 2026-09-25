with items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select * from {{ ref('fct_orders') }}
),

seller_orders as (
    select distinct
        i.seller_id,
        o.order_id,
        cast(date_trunc('month', o.purchased_at) as date) as order_month,
        o.is_late,
        o.review_score
    from items i
    join orders o on o.order_id = i.order_id
),

-- one row per (seller, month) for the revenue side
item_rev as (
    select
        i.seller_id,
        cast(date_trunc('month', o.purchased_at) as date) as order_month,
        count(*)              as n_items,
        sum(i.item_revenue)   as revenue
    from items i
    join orders o on o.order_id = i.order_id
    group by 1, 2
),

monthly as (
    select
        so.seller_id,
        so.order_month,
        count(so.order_id)                 as n_orders,
        count(*) filter (where so.is_late) as n_late,
        count(so.is_late)                  as n_late_known,
        avg(so.review_score)               as avg_review,
        count(so.review_score)             as n_reviews
    from seller_orders so
    group by 1, 2
)

select
    m.seller_id,
    m.order_month,
    m.n_orders,
    r.n_items,
    r.revenue,
    m.n_late,
    m.n_late_known,
    m.n_late * 1.0 / nullif(m.n_late_known, 0) as late_rate,
    m.avg_review,
    m.n_reviews
from monthly m
left join item_rev r
       on r.seller_id   = m.seller_id
      and r.order_month = m.order_month
