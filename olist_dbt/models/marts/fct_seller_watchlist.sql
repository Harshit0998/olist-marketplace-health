{#
    Seller watchlist — a RELATIVE risk rule.

    Each month, rank eligible sellers by their trailing-six-month late rate and
    flag the worst slice. The rule re-reads the market every month, so it cannot
    drift the way an absolute threshold does.

    Why relative: an absolute cut of "late rate above 8%" was tested first. It
    reached lift 2.11 on the training period and collapsed to 1.12 out of time,
    because the marketplace late rate tripled (3.2% -> 11.0%) between mid-2017
    and early 2018. The rule had learned that 8% was unusual, which was a fact
    about 2017 rather than about sellers. Ranking survived: lift 1.60 on train,
    1.51 on the Feb-May 2018 holdout. See docs/findings.md.
#}

{% set flag_percentile = 0.85 %}   {# flag the worst 15% of eligible sellers #}
{% set min_obs_known   = 30   %}   {# enough deliveries to read a rate from    #}

with panel as (

    select * from {{ ref('fct_seller_snapshots') }}

),

market as (

    -- the marketplace-wide late rate inside each snapshot's observation window,
    -- so a seller can be read against the conditions they actually traded in
    select snapshot_month,
           sum(obs_late) * 1.0 / nullif(sum(obs_known), 0) as mkt_late_rate
    from panel
    group by snapshot_month

),

ranked as (

    -- ranking happens only among sellers with enough volume to judge.
    -- percent_rank is ascending, so the worst late rate approaches 1.
    select snapshot_month,
           seller_id,
           row_number()   over (partition by snapshot_month
                                order by obs_late_rate desc, obs_known desc) as rank_in_month,
           count(*)       over (partition by snapshot_month)                 as n_eligible,
           percent_rank() over (partition by snapshot_month
                                order by obs_late_rate)                      as pct_rank
    from panel
    where obs_known >= {{ min_obs_known }}

)

select p.snapshot_month,
       p.seller_id,
       p.state,
       p.city,

       -- what we knew at the snapshot
       p.obs_known,
       p.obs_late,
       p.obs_late_rate,
       m.mkt_late_rate,
       p.obs_late_rate / nullif(m.mkt_late_rate, 0)   as late_rate_vs_market,

       -- position within the month
       r.rank_in_month,
       r.n_eligible,
       r.pct_rank,
       (p.obs_known >= {{ min_obs_known }})           as is_eligible,
       coalesce(r.pct_rank >= {{ flag_percentile }}, false) as is_flagged,

       -- what happened next (for backtesting only; not available at flag time)
       p.perf_known,
       p.perf_late,
       p.perf_late_rate,
       p.is_bad,

       case when p.snapshot_month <= date '2018-01-01'
            then 'train' else 'holdout' end           as period

from panel p
left join market m on m.snapshot_month = p.snapshot_month
left join ranked r on r.snapshot_month = p.snapshot_month
                  and r.seller_id      = p.seller_id
order by p.snapshot_month, r.rank_in_month
