with customers as (
    select * from {{ ref('stg_customers') }}
),

orders as (
    select * from {{ ref('fct_orders') }}
),

-- one row per ORDER, carrying both the person key and the order facts
person_orders as (
    select
        c.customer_unique_id,
        c.customer_id,
        c.city,                     
        c.state,
        o.order_id,
        o.purchased_at,
        o.order_revenue
    from customers c
    join orders o on o.customer_id = c.customer_id
),

agg as (
    select
        po.customer_unique_id, 
        count(po.order_id)      as n_orders,
        min(po.purchased_at)    as first_order_at,
        max(po.purchased_at)    as last_order_at,
        sum(po.order_revenue)   as lifetime_revenue
    from person_orders po
    group by po.customer_unique_id
),

ranked as (
    select
        po.customer_unique_id,
        po.city,
        po.state,
        row_number() over (
            partition by po.customer_unique_id
            order by po.purchased_at desc, po.customer_id
        ) as rn
    from person_orders po
),

latest as (
    select customer_unique_id, city, state
    from ranked
    where rn = 1
)

select
    a.customer_unique_id,
    l.city,
    l.state,
    a.n_orders,
    a.first_order_at,
    a.last_order_at,
    a.lifetime_revenue,
    a.n_orders > 1 as is_repeat
from agg a
join latest l on l.customer_unique_id = a.customer_unique_id