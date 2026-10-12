"""
Regenerate every figure in docs/img/ from the marts.

Before this existed, two images sat in the repo with nothing that produced
them - the same problem as a spreadsheet nobody can rebuild. Every chart here
reads from main_marts, so a figure can never quietly disagree with the model
behind it.

    python scripts/05_charts.py

Colours follow one palette throughout: a single blue for one-series charts,
blue and orange where two series must be told apart. No chart uses two y-axes -
two measures on different scales get two panels instead, because a dual axis
lets the author put the crossover wherever the story needs it.
"""
from pathlib import Path
import duckdb
import matplotlib
matplotlib.use("Agg")                      # no display on a CI runner
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
DB   = ROOT / "olist.duckdb"
OUT  = ROOT / "docs" / "img"

# ---------------------------------------------------------------- palette ---
SURFACE   = "#fcfcfb"
INK       = "#0b0b0b"
INK_2     = "#52514e"
MUTED     = "#898781"
GRID      = "#e1e0d9"
BASELINE  = "#c3c2b7"
BLUE      = "#2a78d6"
ORANGE    = "#eb6834"
RED       = "#d03b3b"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "font.size": 10,
    "font.family": "DejaVu Sans",
    "axes.edgecolor": BASELINE, "axes.labelcolor": INK_2,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.titlecolor": INK, "axes.titlesize": 12,
    "axes.titleweight": "semibold", "axes.titlelocation": "left",
    "axes.titlepad": 14,
})


def style(ax, ygrid=True, xgrid=False):
    """Recessive chrome: no box, hairline grid on the measured axis only."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(BASELINE)
    ax.spines["bottom"].set_color(BASELINE)
    ax.set_axisbelow(True)
    if ygrid:
        ax.grid(axis="y", color=GRID, linewidth=0.8)
    if xgrid:
        ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.tick_params(length=0)


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  {name:<34}{path.stat().st_size // 1024:>5} KB")


pct = FuncFormatter(lambda v, _: f"{v:.0%}")


# ------------------------------------------------------------------ charts ---
def monthly_overview(con):
    """GMV and orders share an x-axis but never a y-axis - two panels, not two scales."""
    d = con.execute("""
        select order_month, gmv, n_orders from main_marts.fct_monthly
        where order_month >= date '2017-01-01' and order_month < date '2018-09-01'
        order by order_month
    """).df()

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True,
                                 gridspec_kw={"hspace": 0.35})

    a1.plot(d.order_month, d.gmv / 1e6, color=BLUE, linewidth=2)
    a1.set_title("Revenue peaked in November 2017 and never recovered")
    a1.set_ylabel("GMV (R$ m)")
    # zero baseline: a truncated y-axis would exaggerate the plateau
    a1.set_ylim(0, (d.gmv / 1e6).max() * 1.30)
    a1.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1f}"))
    style(a1)

    a2.bar(d.order_month, d.n_orders, width=20, color=BLUE)
    a2.set_ylim(0, d.n_orders.max() * 1.22)
    a2.set_title("Orders per month")
    a2.set_ylabel("orders")
    a2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    style(a2)

    # the peak is the point of the chart, so label it rather than leave it to be found
    peak = d.loc[d.n_orders.idxmax()]
    for ax, val, txt in ((a1, peak.gmv / 1e6, f"R$ {peak.gmv/1e6:.2f}m"),
                         (a2, peak.n_orders, f"{peak.n_orders:,} orders")):
        ax.annotate(f"Nov 2017 — {txt}", xy=(peak.order_month, val),
                    xytext=(0, 12), textcoords="offset points",
                    ha="center", color=INK_2, fontsize=9)
    save(fig, "monthly_overview.png")


def cohort_retention(con):
    """The censoring trap: the naive measure falls, the fixed-horizon one does not."""
    d = con.execute("""
        with per_cohort as (
            select cohort_month,
                   max(cohort_size)                                         as size,
                   sum(n_active) filter (where month_number between 1 and 3) as back_3m,
                   sum(n_active) filter (where month_number >= 1)            as back_ever,
                   max(month_number)                                         as observed_months
            from main_marts.fct_cohort_retention
            group by cohort_month
        )
        select cohort_month,
               back_ever * 1.0 / size as naive_ever_returned,
               case when observed_months >= 3 then back_3m * 1.0 / size end as fixed_3_month
        from per_cohort order by cohort_month
    """).df()

    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.plot(d.cohort_month, d.naive_ever_returned, color=ORANGE, linewidth=2,
            label="Ever returned (naive)")
    ax.plot(d.cohort_month, d.fixed_3_month, color=BLUE, linewidth=2,
            label="Returned within 3 months")
    ax.set_title("The retention collapse is an artefact of how long we watched")
    ax.set_ylabel("share of the cohort")
    ax.yaxis.set_major_formatter(pct)
    ax.set_ylim(0, None)
    ax.legend(frameon=False, loc="upper right", labelcolor=INK_2)
    style(ax)

    first, last = d.iloc[0], d.dropna(subset=["naive_ever_returned"]).iloc[-1]
    ax.annotate(f"{first.naive_ever_returned:.1%}",
                xy=(first.cohort_month, first.naive_ever_returned),
                xytext=(6, 6), textcoords="offset points", color=ORANGE, fontsize=9)
    ax.annotate(f"{last.naive_ever_returned:.1%}",
                xy=(last.cohort_month, last.naive_ever_returned),
                xytext=(-28, 8), textcoords="offset points", color=ORANGE, fontsize=9)
    mean3 = d.fixed_3_month.mean()
    ax.annotate(f"flat, mean {mean3:.2%}", xy=(d.cohort_month.iloc[3], mean3),
                xytext=(0, -20), textcoords="offset points",
                ha="center", color=BLUE, fontsize=9)
    save(fig, "cohort_retention.png")


def review_by_delay_band(con):
    """Dose-response. One series, so one colour and no legend - the title names it."""
    d = con.execute("select delay_band, avg_review, n_orders "
                    "from main_marts.fct_delay_bands order by band_order").df()

    fig, ax = plt.subplots(figsize=(8, 4.4))
    bars = ax.bar(d.delay_band, d.avg_review, color=BLUE, width=0.62)
    ax.set_title("Every extra day late costs review score, and the first days cost most")
    ax.set_ylabel("average review score")
    ax.set_ylim(0, 5)
    style(ax)

    for bar, score, n in zip(bars, d.avg_review, d.n_orders):
        ax.annotate(f"{score:.2f}", xy=(bar.get_x() + bar.get_width() / 2, score),
                    xytext=(0, 5), textcoords="offset points",
                    ha="center", color=INK, fontsize=10, fontweight="semibold")
        ax.annotate(f"n={n:,}", xy=(bar.get_x() + bar.get_width() / 2, 0),
                    xytext=(0, 6), textcoords="offset points",
                    ha="center", color="#ffffff", fontsize=8)
    save(fig, "review_by_delay_band.png")


def late_rate_by_state(con):
    """Rank, with the marketplace rate as the reference the eye needs."""
    d = con.execute("""
        select state, late_rate, n_orders from main_marts.fct_delivery_by_state
        order by late_rate
    """).df()
    overall = con.execute("""
        select sum(n_late) * 1.0 / sum(n_orders) from main_marts.fct_delivery_by_state
    """).fetchone()[0]

    fig, ax = plt.subplots(figsize=(8, 7))
    ax.barh(d.state, d.late_rate, color=BLUE, height=0.68)
    ax.axvline(overall, color=RED, linewidth=1.5, linestyle="--")
    ax.annotate(f"marketplace {overall:.1%}", xy=(overall, len(d) - 0.2),
                xytext=(6, 0), textcoords="offset points",
                color=RED, fontsize=9, va="center")
    ax.set_title("Late rate by customer state")
    ax.set_xlabel("share of delivered orders arriving late")
    ax.xaxis.set_major_formatter(pct)
    style(ax, ygrid=False, xgrid=True)

    for y, (rate, n) in enumerate(zip(d.late_rate, d.n_orders)):
        ax.annotate(f"{rate:.1%}  ({n:,} orders)", xy=(rate, y),
                    xytext=(5, 0), textcoords="offset points",
                    va="center", color=INK_2, fontsize=8)
    ax.set_xlim(0, d.late_rate.max() * 1.45)
    save(fig, "late_rate_by_state.png")


def watchlist_drift(con):
    """Why the absolute rule died: the yardstick moved and the outcome moved the other way."""
    d = con.execute("""
        select snapshot_month,
               max(mkt_late_rate) as market_late_rate,
               count(*) filter (where obs_late_rate > 0.08 and obs_known >= 30)
                   * 1.0 / count(*)                       as flagged_by_absolute_rule,
               count(*) filter (where is_bad) * 1.0 / count(*) as actually_bad
        from main_marts.fct_seller_watchlist
        group by snapshot_month order by snapshot_month
    """).df()

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(d.snapshot_month, d.flagged_by_absolute_rule, color=ORANGE, linewidth=2,
            label="Flagged by a fixed 8% threshold")
    ax.plot(d.snapshot_month, d.actually_bad, color=BLUE, linewidth=2,
            label="Actually went bad")
    ax.plot(d.snapshot_month, d.market_late_rate, color=MUTED, linewidth=2,
            linestyle="--", label="Marketplace late rate")
    ax.set_title("A fixed threshold measures the market, not the seller")
    ax.set_ylabel("share of sellers")
    ax.yaxis.set_major_formatter(pct)
    ax.set_ylim(0, None)
    ax.legend(frameon=False, loc="upper left", labelcolor=INK_2)
    style(ax)
    save(fig, "watchlist_drift.png")


def main():
    if not DB.exists():
        raise SystemExit(f"{DB.name} not found - run scripts/01_load_raw.py and dbt build first.")
    con = duckdb.connect(str(DB), read_only=True)
    print("writing figures to docs/img/\n")
    for fn in (monthly_overview, cohort_retention, review_by_delay_band,
               late_rate_by_state, watchlist_drift):
        fn(con)
    con.close()
    print("\ndone")


if __name__ == "__main__":
    main()
