-- The point of a relative rule is that the size of the list does not move with
-- market conditions. This test encodes that promise: in every snapshot, between
-- 10% and 20% of eligible sellers are flagged.
--
-- The absolute rule this replaced would fail here outright - it flagged 2.5% of
-- sellers in Aug 2017 and 39.8% in Mar 2018.

with by_month as (
    select snapshot_month,
           count(*) filter (where is_eligible)               as n_eligible,
           count(*) filter (where is_flagged)                as n_flagged
    from {{ ref('fct_seller_watchlist') }}
    group by snapshot_month
)

select snapshot_month,
       n_eligible,
       n_flagged,
       n_flagged * 1.0 / nullif(n_eligible, 0) as flag_rate
from by_month
where n_flagged * 1.0 / nullif(n_eligible, 0) not between 0.10 and 0.20
