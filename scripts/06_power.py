"""
Power analysis for the experiment designed in docs/experiment_design.md.

Every input here is measured from the marts rather than assumed, which is the
only reason the answer is worth anything: the usual portfolio A/B section picks
a baseline and a lift out of the air, and the sample size it produces is
therefore arbitrary.

Two candidate designs are sized:

  A  randomise the sellers on the watchlist, measure next-quarter late rate
  B  randomise their orders, warn the buyer early, measure review score

A is the obvious design and it turns out to be hopeless at this marketplace's
scale. Showing that is the point - an experiment that cannot detect a plausible
effect should be killed at the design stage, not after it has run.

    python scripts/06_power.py
"""
from pathlib import Path
import math
import duckdb

from chartstyle import apply, style, BLUE, ORANGE, MUTED, INK_2, GRID, save

ROOT = Path(__file__).resolve().parents[1]
DB   = ROOT / "olist.duckdb"
OUT  = ROOT / "docs" / "img"

ALPHA, POWER = 0.05, 0.80
# two-sided test: 1.96 at 5%, 0.84 for 80% power. Hard-coded rather than pulled
# from scipy so the numbers are visible and the script has no extra dependency.
Z = 1.959964 + 0.841621

apply()


def mde(sd, n_per_arm):
    """Smallest difference in means detectable at ALPHA with POWER."""
    return Z * sd * math.sqrt(2 / n_per_arm) if n_per_arm >= 2 else float("inf")


def n_required(sd, effect):
    """Units per arm needed to detect `effect`."""
    return math.ceil(2 * (Z * sd / effect) ** 2)


def baselines(con):
    a = con.execute("""
        select count(distinct seller_id), avg(perf_late_rate), stddev(perf_late_rate),
               corr(obs_late_rate, perf_late_rate)
        from main_marts.fct_seller_watchlist where is_flagged
    """).fetchone()

    b = con.execute("""
        with flagged as (
            select distinct seller_id, snapshot_month
            from main_marts.fct_seller_watchlist where is_flagged
        ),
        o as (
            select distinct fo.order_id, fo.is_late, fo.review_score
            from main_marts.fct_orders fo
            join main_staging.stg_order_items oi on oi.order_id = fo.order_id
            join flagged f on f.seller_id = oi.seller_id
                          and f.snapshot_month = date_trunc('month', fo.purchased_at)
            where fo.purchased_at >= date '2017-06-01'
              and fo.purchased_at <  date '2018-06-01'
        )
        select count(*), avg(review_score), stddev(review_score),
               avg(case when is_late then 1.0 else 0 end)
        from o where review_score is not null
    """).fetchone()

    # what happens to flagged sellers with no intervention at all - the number
    # that makes a control arm non-negotiable
    rtm = con.execute("""
        select avg(obs_late_rate), avg(perf_late_rate)
        from main_marts.fct_seller_watchlist where is_flagged
    """).fetchone()

    return dict(
        a_sellers=a[0], a_mu=a[1], a_sd=a[2], a_corr=a[3],
        b_orders=b[0], b_mu=b[1], b_sd=b[2], b_late=b[3],
        rtm_before=rtm[0], rtm_after=rtm[1],
    )


def report(d):
    MONTHS = 12
    a_rate = d["a_sellers"] / MONTHS          # new distinct sellers per month
    b_rate = d["b_orders"] / MONTHS           # reviewed orders per month

    print("Measured from the marts, not assumed\n" + "-" * 64)
    print(f"regression to the mean among flagged sellers, no intervention:")
    print(f"   late rate {d['rtm_before']:.1%} when flagged -> {d['rtm_after']:.1%} "
          f"a quarter later  ({d['rtm_after'] - d['rtm_before']:+.1%})")
    print(f"   corr(before, after) = {d['a_corr']:+.3f}\n")

    print(f"DESIGN A  sellers on the watchlist, outcome = next-quarter late rate")
    print(f"   accrual {a_rate:.0f} distinct sellers/month · baseline {d['a_mu']:.1%} "
          f"· SD {d['a_sd']:.3f}")
    for mo in (3, 6, 12, 24):
        per = int(a_rate * mo / 2)
        m = mde(d["a_sd"], per)
        print(f"   {mo:>2} months -> {per:>6,}/arm   MDE {m:.1%} absolute "
              f"({m / d['a_mu']:.0%} relative)")
    print(f"   to detect a 20% relative effect: "
          f"{n_required(d['a_sd'], 0.20 * d['a_mu']):,} sellers per arm\n")

    print(f"DESIGN B  their orders, outcome = review score")
    print(f"   accrual {b_rate:.0f} reviewed orders/month · baseline {d['b_mu']:.2f} "
          f"· SD {d['b_sd']:.2f} · late rate {d['b_late']:.1%}")
    for mo in (1, 3, 6, 12):
        per = int(b_rate * mo / 2)
        m = mde(d["b_sd"], per)
        print(f"   {mo:>2} months -> {per:>6,}/arm   MDE {m:.3f} stars "
              f"({m / d['b_mu']:.0%} relative)")
    print(f"   to detect a 0.20-star effect: "
          f"{n_required(d['b_sd'], 0.20):,} orders per arm")


def chart(d):
    MONTHS = 12
    a_rate = d["a_sellers"] / MONTHS
    b_rate = d["b_orders"] / MONTHS
    xs = [m / 2 for m in range(2, 49)]        # 1 to 24 months, half-month steps

    a = [mde(d["a_sd"], max(int(a_rate * m / 2), 2)) / d["a_mu"] for m in xs]
    b = [mde(d["b_sd"], max(int(b_rate * m / 2), 2)) / d["b_mu"] for m in xs]

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 5))

    # the band of effects an intervention of this kind plausibly delivers
    ax.axhspan(0.05, 0.20, color=GRID, zorder=0)
    ax.annotate("effects an intervention like this plausibly delivers",
                xy=(23.2, 0.125), ha="right", color=MUTED, fontsize=9)

    ax.plot(xs, a, color=ORANGE, linewidth=2, label="A · sellers, late rate")
    ax.plot(xs, b, color=BLUE,   linewidth=2, label="B · orders, review score")
    ax.set_title("How long each design must run to detect an effect worth having")
    ax.set_xlabel("months of runtime")
    ax.set_ylabel("smallest detectable effect, relative to baseline")
    ax.set_ylim(0, 1.0)
    ax.set_xlim(1, 24)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.legend(frameon=False, loc="upper right", labelcolor=INK_2)
    style(ax)

    # B is inside the band from the first month; A is never inside it
    cross = next((x for x, y in zip(xs, b) if y <= 0.20), None)
    if cross is not None:
        label = ("B is inside the band from month one"
                 if cross <= 1.5 else f"B reaches the band at {cross:.0f} months")
        ax.annotate(label, xy=(5, b[8]), xytext=(6, 46), textcoords="offset points",
                    color=BLUE, fontsize=9,
                    arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=0.8))
    ax.annotate("A is still at 34% after two years",
                xy=(xs[-1], a[-1]), xytext=(-8, 16), textcoords="offset points",
                ha="right", color=ORANGE, fontsize=9)

    save(fig, OUT / "experiment_power.png")


def main():
    if not DB.exists():
        raise SystemExit(f"{DB.name} not found - run the loader and dbt build first.")
    con = duckdb.connect(str(DB), read_only=True)
    d = baselines(con)
    con.close()
    report(d)
    print()
    chart(d)


if __name__ == "__main__":
    main()
