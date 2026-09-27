with orders as (
    select
        o.*,
        c.customer_unique_id,
        cast(date_trunc('month', o.purchased_at) as date) as order_month
    from {{ ref('fct_orders') }} o
    join {{ ref('stg_customers') }} c on c.customer_id = o.customer_id
),

monthly as (
    select  
        o.order_month,
        count(o.order_id)                       as n_orders,
        count(distinct o.customer_unique_id)    as n_customers,
        sum(o.n_items)                          as n_items,
        sum(o.order_revenue)                    as gmv,
        count(*) filter (where o.is_late)       as n_late,
        count(o.is_late)                        as n_late_known,
        avg(o.review_score)                     as avg_review,
        count(o.review_score)                   as n_reviews

    from orders o
    group by o.order_month
),

new_customers as (
    select
        cast(date_trunc('month', first_order_at) as date) as order_month,
        count(*) as n_new_customers
    from {{ ref('dim_customers') }}
    group by 1   
)

select
    m.*,
    coalesce(nc.n_new_customers, 0)                  as n_new_customers,
    m.n_customers - coalesce(nc.n_new_customers, 0)  as n_returning_customers,
    m.gmv * 1.0   / nullif(m.n_orders, 0)            as aov,
    m.n_late * 1.0 / nullif(m.n_late_known, 0)       as late_rate
from monthly m 
left join new_customers nc on m.order_month = nc.order_month
order by m.order_month