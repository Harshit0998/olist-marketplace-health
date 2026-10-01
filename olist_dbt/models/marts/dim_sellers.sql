with sellers as (
    select * from {{ ref('stg_sellers') }}
),

items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select * from {{ ref('fct_orders') }}
),

-- one row per (seller, order) — a seller can have several item lines on one order
seller_orders as (
    select distinct
        i.seller_id,
        o.order_id,
        o.purchased_at,
        o.is_late,
        o.review_score
    from items i
    join orders o on o.order_id = i.order_id
),


order_stats as (
    select
        so.seller_id,
        count(so.order_id)      as n_orders,
        min(so.purchased_at)    as first_sale_at,
        max(so.purchased_at)    as last_sale_at,
        count(*) filter (where so.is_late) as n_late,
        count(so.is_late)                  as n_late_known,
        avg(so.review_score)    as avg_review
    from seller_orders so
    group by so.seller_id
),

item_stats as (
    select
        i.seller_id,
        count(*)                    as n_items,
        sum(i.item_revenue)         as total_revenue
    from items i 
    group by i.seller_id
)

select
    s.seller_id,
    s.city,
    s.state,
    os.n_orders,
    os.first_sale_at,
    os.last_sale_at,
    it.n_items,
    it.total_revenue,
    os.avg_review,
    os.n_late * 1.0 / nullif(os.n_late_known, 0) as late_rate

from sellers s
left join order_stats os on os.seller_id = s.seller_id
left join item_stats  it on it.seller_id = s.seller_id