with orders as (
    select * from {{ ref('stg_orders') }}
),

items as (
    select order_id,
           count(*)          as n_items,
           count(distinct product_id) as n_products,
           count(distinct seller_id)  as n_sellers,
           sum(item_revenue) as order_revenue
    from {{ ref('stg_order_items') }}
    group by order_id
),

payments as (
    select order_id,
           count(*)           as n_payments,
           sum(payment_amount) as payment_total
    from {{ ref('stg_order_payments') }}
    group by order_id
),

reviews as (
    select order_id, review_score
    from {{ref('stg_order_reviews')}}
)

select
    o.order_id,
    o.customer_id,
    o.order_status,
    o.purchased_at,
    o.approved_at,
    o.shipped_at,
    o.delivered_at,
    o.estimated_delivery_at,
    o.is_late,
    o.delivery_days,
    o.delay_days,
    coalesce(i.n_items, 0)    as n_items,
    i.n_products,
    i.n_sellers,
    i.order_revenue,
    p.n_payments,
    p.payment_total,
    r.review_score,
    r.order_id is not null as has_review

from orders o
left join items    i on i.order_id = o.order_id
left join payments p on p.order_id = o.order_id
left join reviews  r on r.order_id = o.order_id