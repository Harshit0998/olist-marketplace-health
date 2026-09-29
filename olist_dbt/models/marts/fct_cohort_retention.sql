with customers as (
    select
        customer_unique_id,
        cast(date_trunc('month', first_order_at) as date) as cohort_month
    from {{ ref('dim_customers') }}
    where first_order_at >= '2017-01-01'
      and first_order_at <  '2018-09-01'
),

orders as (
    select
        c.customer_unique_id,
        c.cohort_month,
        cast(date_trunc('month', o.purchased_at) as date) as order_month
    from {{ ref('fct_orders') }} o
    join {{ ref('stg_customers') }} sc on sc.customer_id = o.customer_id
    join customers c on c.customer_unique_id = sc.customer_unique_id
    where o.purchased_at < '2018-09-01'
),

cohort_size as (
    select cohort_month, count(*) as cohort_size
    from customers
    group by 1
),

-- TODO 1: one row per (cohort_month, month_number) with the number of
-- DISTINCT customers from that cohort who ordered in that month.
--   month_number = date_diff('month', cohort_month, order_month)
-- Source is the `orders` CTE. Month 0 is the cohort's own month.
activity as (
    select
        o.cohort_month,
        date_diff('month',o.cohort_month,o.order_month) as month_number,
        count(DISTINCT o.customer_unique_id)            as n_active    
    from orders o
    group by 1,2
),

-- the spine: every combination that COULD have been observed
spine as (
    select
        s.cohort_month,
        s.cohort_size,
        m.month_number
    from cohort_size s
    cross join (select unnest(generate_series(0, 20)) as month_number) m
    where m.month_number <= date_diff('month', s.cohort_month, date '2018-08-01')
)

select
    sp.cohort_month,
    sp.month_number,
    sp.cohort_size,
    coalesce(a.n_active, 0)                            as n_active,
    coalesce(a.n_active, 0) * 1.0 / sp.cohort_size     as retention
from spine sp
left join activity a
       on a.cohort_month = sp.cohort_month
      and a.month_number = sp.month_number
order by sp.cohort_month, sp.month_number