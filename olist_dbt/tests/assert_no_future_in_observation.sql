-- Leakage test: no future data may reach the observation features.
--
-- orders_to_date counts everything a seller had done up to and including the
-- snapshot month. It is built with a single bound (<= snapshot) and no window
-- length, so it does not reuse the model's window arithmetic. If the
-- observation window ever reached forward into the performance period,
-- obs_orders would exceed that cumulative total and this test fires.
--
-- Returns rows only when the panel is contaminated.

with to_date as (
    select sn.snapshot_month,
           f.seller_id,
           sum(f.n_orders) as orders_to_date
    from (select distinct snapshot_month from {{ ref('fct_seller_snapshots') }}) sn
    join {{ ref('fct_seller_monthly') }} f
      on f.order_month <= sn.snapshot_month
    group by sn.snapshot_month, f.seller_id
)

select s.snapshot_month,
       s.seller_id,
       s.obs_orders,
       t.orders_to_date
from {{ ref('fct_seller_snapshots') }} s
join to_date t
  on t.snapshot_month = s.snapshot_month
 and t.seller_id      = s.seller_id
where s.obs_orders > t.orders_to_date
