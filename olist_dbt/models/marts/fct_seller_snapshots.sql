-- One row per seller per monthly snapshot.
-- LEFT of the snapshot: what we knew at that moment  (observation window, 6 months)
-- RIGHT of the snapshot: what then happened          (performance window, 3 months)
-- Nothing from the right may ever appear on the left.

with snapshots as (
    select unnest(generate_series(date '2017-06-01',
                                  date '2018-05-01',
                                  interval 1 month))::date as snapshot_month
),

-- the complete grid: every seller considered at every snapshot.
-- fct_seller_monthly is sparse, so we aggregate ONTO this, not FROM it.
grid as (
    select sn.snapshot_month,
           s.seller_id
    from snapshots sn
    cross join (select distinct seller_id from {{ ref('fct_seller_monthly') }}) s
),

-- ===========================================================================
-- TODO 1 — the OBSERVATION window
--
-- The 6 months ENDING AT the snapshot month, inclusive of it. For October 2017
-- that is May, Jun, Jul, Aug, Sep, Oct.
--
-- Join fct_seller_monthly to grid on seller_id, restricted to that month range,
-- then group by snapshot_month, seller_id and produce:
--
--   obs_orders         total orders placed
--   obs_known          delivered orders where lateness is known   (n_late_known)
--   obs_late           late orders                                 (n_late)
--   obs_revenue        revenue
--   obs_items          items
--   obs_reviews        number of reviews                           (n_reviews)
--   obs_review_points  >>> the weighted numerator for average review.
--                          avg(avg_review) is WRONG. Work out what is right.
--   obs_active_months  how many of the 6 months had at least one order
--
-- Use a LEFT JOIN from grid, so a seller with no trading in the window still
-- gets a row (with zeros) rather than vanishing.
-- ===========================================================================
obs as (
    select g.snapshot_month,
           g.seller_id,

           coalesce(sum(f.n_orders),     0)             as obs_orders,
           coalesce(sum(f.n_late_known), 0)             as obs_known,
           coalesce(sum(f.n_late),       0)             as obs_late,
           coalesce(sum(f.revenue),      0)             as obs_revenue,
           coalesce(sum(f.n_items),      0)             as obs_items,
           coalesce(sum(f.n_reviews),    0)             as obs_reviews,

           -- weighted numerator for the average review. Each month contributes
           -- its TOTAL review points, not its average: avg(avg_review) would
           -- give a month with 2 reviews the same weight as a month with 200.
           coalesce(sum(f.avg_review * f.n_reviews), 0) as obs_review_points,

           -- a row exists only in months the seller traded, so counting the
           -- non-NULL month labels counts the active months
           count(f.order_month)                         as obs_active_months

    from grid g
    left join {{ ref('fct_seller_monthly') }} f
           on f.seller_id   = g.seller_id
          and f.order_month >= g.snapshot_month - interval 5 month
          and f.order_month <= g.snapshot_month
    group by g.snapshot_month, g.seller_id
),

-- ===========================================================================
-- TODO 2 — the PERFORMANCE window
--
-- The 3 months AFTER the snapshot month. For October 2017: Nov, Dec, Jan.
-- Same join shape. Produce:
--
--   perf_orders        total orders
--   perf_known         delivered orders where lateness is known
--   perf_late          late orders
-- ===========================================================================
perf as (
    select g.snapshot_month,
           g.seller_id,

           coalesce(sum(f.n_orders),     0) as perf_orders,
           coalesce(sum(f.n_late_known), 0) as perf_known,
           coalesce(sum(f.n_late),       0) as perf_late

    from grid g
    left join {{ ref('fct_seller_monthly') }} f
           on f.seller_id   = g.seller_id
          and f.order_month >= g.snapshot_month + interval 1 month
          and f.order_month <= g.snapshot_month + interval 3 month
    group by g.snapshot_month, g.seller_id
),

-- the seller's first trading month AS KNOWN AT the snapshot.
-- Note we do NOT use dim_sellers.first_sale_at: that is computed over all time,
-- and a feature built from all time is a leak waiting to happen.
tenure as (
    select g.snapshot_month,
           g.seller_id,
           min(f.order_month) as first_month
    from grid g
    join {{ ref('fct_seller_monthly') }} f
      on f.seller_id = g.seller_id
     and f.order_month <= g.snapshot_month
    group by 1, 2
),

joined as (
    select g.snapshot_month,
           g.seller_id,
           s.state,
           s.city,

           -- observation-window features
           o.obs_orders,
           o.obs_known,
           o.obs_late,
           o.obs_revenue,
           o.obs_items,
           o.obs_reviews,
           o.obs_review_points,
           o.obs_active_months,
           date_diff('month', t.first_month, g.snapshot_month) as tenure_months,

           -- performance-window outcome
           p.perf_orders,
           p.perf_known,
           p.perf_late

    from grid g
    left join obs    o on o.snapshot_month = g.snapshot_month and o.seller_id = g.seller_id
    left join perf   p on p.snapshot_month = g.snapshot_month and p.seller_id = g.seller_id
    left join tenure t on t.snapshot_month = g.snapshot_month and t.seller_id = g.seller_id
    left join {{ ref('dim_sellers') }} s on s.seller_id = g.seller_id
)

select snapshot_month,
       seller_id,
       state,
       city,
       tenure_months,

       obs_orders,
       obs_known,
       obs_late,
       obs_revenue,
       obs_items,
       obs_reviews,
       obs_active_months,

       -- derived features
       obs_late * 1.0        / nullif(obs_known, 0)   as obs_late_rate,
       obs_review_points * 1.0 / nullif(obs_reviews, 0) as obs_avg_review,
       obs_revenue           / nullif(obs_orders, 0)  as obs_aov,
       obs_items * 1.0       / nullif(obs_orders, 0)  as obs_items_per_order,

       -- outcome
       perf_orders,
       perf_known,
       perf_late,
       perf_late * 1.0 / nullif(perf_known, 0)        as perf_late_rate,
       (perf_late * 1.0 / nullif(perf_known, 0)) > 0.10 as is_bad

from joined
-- eligibility: enough history to build features on, enough future to judge by
where obs_known  >= 10
  and perf_known >= 5
order by snapshot_month, seller_id
