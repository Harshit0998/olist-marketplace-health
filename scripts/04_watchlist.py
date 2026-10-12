"""
Seller watchlist: a threshold rule instead of a scorecard.

The rule is CHOSEN on the training period (snapshots up to Jan 2018) and then
evaluated ONCE on the holdout (Feb-May 2018). A threshold picked by looking at
the holdout has been fitted to it, and the number you would quote afterwards is
not a forecast of anything.

Run:  python scripts/04_watchlist.py
"""
from pathlib import Path
import duckdb
import pandas as pd

DB = Path(__file__).resolve().parents[1] / "olist.duckdb"
TRAIN_END = "2018-01-01"

# grid searched on training data
RATE_CUTS = [0.06, 0.08, 0.10, 0.12, 0.15]
MIN_KNOWN = [20, 30]

# the rule we settled on, 12 Oct 2026
RULE_RATE = 0.08
RULE_MIN_OBS = 30


def counts(con, rate, min_obs, period_sql, extra_sql=""):
    """Return (n, n_bad, n_flagged, hits) for one rule over one slice."""
    return con.execute(f"""
        select count(*),
               count(*) filter (where is_bad),
               count(*) filter (where obs_late_rate > {rate} and obs_known >= {min_obs}),
               count(*) filter (where obs_late_rate > {rate} and obs_known >= {min_obs}
                                  and is_bad)
        from main_marts.fct_seller_snapshots
        where {period_sql} {extra_sql}
    """).fetchone()


def metrics(n, n_bad, n_flagged, hits):
    """Turn raw counts into the rates we actually read."""
    base = n_bad / n
    hit = hits / n_flagged if n_flagged else None
    return {
        "flagged":  n_flagged,
        "flag%":    round(100 * n_flagged / n, 1),
        "hit%":     round(100 * hit, 1) if hit is not None else None,
        "catch%":   round(100 * hits / n_bad, 1) if n_bad else None,
        # the most any rule flagging this many rows could possibly catch
        "ceiling%": round(100 * min(n_flagged / n_bad, 1), 1) if n_bad else None,
        "lift":     round(hit / base, 2) if hit is not None else None,
    }


TRAIN = f"snapshot_month <= date '{TRAIN_END}'"
TEST  = f"snapshot_month >  date '{TRAIN_END}'"


def header(con, label, period_sql, extra_sql=""):
    n, n_bad, _, _ = counts(con, 9, 0, period_sql, extra_sql)   # rule that flags nothing
    print(f"\n{label}")
    print(f"  rows {n:,} · went bad {n_bad:,} · base rate {n_bad / n:.1%}")
    return n, n_bad


def main():
    con = duckdb.connect(str(DB), read_only=True)

    # ---------------------------------------------------------------- train
    header(con, f"TRAINING  (snapshots to {TRAIN_END}) — rule chosen here", TRAIN)
    rows = []
    for min_obs in MIN_KNOWN:
        for rate in RATE_CUTS:
            m = metrics(*counts(con, rate, min_obs, TRAIN))
            rows.append({"rate>": rate, "min_obs": min_obs, **m})
    print()
    print(pd.DataFrame(rows).to_string(index=False))

    # -------------------------------------------------------------- holdout
    print("\n" + "=" * 68)
    print(f"RULE: late rate > {RULE_RATE:.0%} on at least {RULE_MIN_OBS} known deliveries")
    print("=" * 68)

    for label, period in [("train", TRAIN), ("HOLDOUT Feb-May 2018", TEST)]:
        n, n_bad = header(con, label, period)
        m = metrics(*counts(con, RULE_RATE, RULE_MIN_OBS, period))
        print(f"  flags {m['flagged']} ({m['flag%']}%) · "
              f"hit {m['hit%']}% · catch {m['catch%']}% of a possible {m['ceiling%']}% · "
              f"lift {m['lift']}")

    # ------------------------------------------- holdout, unseen sellers only
    unseen = f"and seller_id not in (select seller_id from main_marts.fct_seller_snapshots where {TRAIN})"
    n, n_bad = header(con, "HOLDOUT, sellers never seen in training", TEST, unseen)
    m = metrics(*counts(con, RULE_RATE, RULE_MIN_OBS, TEST, unseen))
    print(f"  flags {m['flagged']} ({m['flag%']}%) · "
          f"hit {m['hit%']}% · catch {m['catch%']}% of a possible {m['ceiling%']}% · "
          f"lift {m['lift']}")

    con.close()
    print("\nceiling% = the most any rule flagging this many rows could catch.")
    print("lift     = hit rate / base rate. 1.0 means no better than guessing.\n")


if __name__ == "__main__":
    main()
