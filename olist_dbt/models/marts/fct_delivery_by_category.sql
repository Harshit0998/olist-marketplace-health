-- One row per product category.
-- An order is attributed to every category it contains. 97.9% of orders hold a
-- single category, 0.74% span two or more and are counted in each, so the order
-- total here slightly exceeds the marketplace total. Documented, not corrected:
-- the alternative (picking one category per order) would invent a rule.

with order_category as (
    select distinct
           i.order_id,
           coalesce(p.category, 'uncategorised') as category
    from {{ ref('stg_order_items') }} i
    join {{ ref('stg_products') }} p on p.product_id = i.product_id
),

orders as (
    select oc.category,
           o.order_id,
           o.is_late,
           o.review_score,
           o.delivery_days
    from {{ ref('fct_orders') }} o
    join order_category oc on oc.order_id = o.order_id
    where o.is_late is not null
)

select
    category,
    count(*)                                                as n_orders,
    count(*) filter (where is_late)                         as n_late,
    count(*) filter (where is_late) * 1.0 / count(*)        as late_rate,

    count(review_score) filter (where not is_late)          as n_reviewed_ontime,
    count(review_score) filter (where     is_late)          as n_reviewed_late,
    sum(review_score)   filter (where not is_late)          as review_points_ontime,
    sum(review_score)   filter (where     is_late)          as review_points_late,

    avg(review_score) filter (where not is_late)            as review_ontime,
    avg(review_score) filter (where     is_late)            as review_late,
    avg(review_score) filter (where not is_late)
      - avg(review_score) filter (where is_late)            as review_gap,

    avg(delivery_days)                                      as avg_delivery_days

from orders
group by category
having count(*) >= 100          -- below this the two-group means are noise
order by n_orders desc
