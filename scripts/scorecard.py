"""
Weight-of-Evidence / Information-Value toolkit for the seller risk scorecard.

Everything here is fitted on the TRAINING period only and then applied to test.
Bin edges learned from test data would be a leak, so the fit/apply split is
enforced by the function signatures: *_fit returns a rule, *_apply uses it.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import duckdb

DB = Path(__file__).resolve().parents[1] / "olist.duckdb"

NUMERIC_FEATURES = [
    "obs_late_rate",
    "obs_avg_review",
    "obs_orders",
    "obs_revenue",
    "obs_aov",
    "obs_items_per_order",
    "obs_active_months",
    "tenure_months",
]
CATEGORICAL_FEATURES = ["state"]
TARGET = "is_bad"
TRAIN_END = pd.Timestamp("2018-01-01")      # last snapshot in the training period


# ---------------------------------------------------------------- data -----
def load_panel(train_end=TRAIN_END):
    """Read the panel and tag each row train/test by snapshot date."""
    con = duckdb.connect(str(DB), read_only=True)
    df = con.execute("select * from main_marts.fct_seller_snapshots").df()
    con.close()
    df["snapshot_month"] = pd.to_datetime(df["snapshot_month"])
    df["split"] = np.where(df["snapshot_month"] <= train_end, "train", "test")
    return df


# ------------------------------------------------------------- binning -----
def fit_numeric_bins(s, n_bins=5):
    """
    Learn quantile cut points from a training series.

    Returns a list of edges. Repeated values (e.g. a pile of sellers at a late
    rate of exactly 0) collapse neighbouring quantiles, so the number of bins
    actually produced may be fewer than n_bins. That is correct behaviour, not
    a failure: you cannot split a mass point.
    """
    _, edges = pd.qcut(s, n_bins, retbins=True, duplicates="drop")
    edges = edges.astype(float)
    edges[0], edges[-1] = -np.inf, np.inf     # so test values outside the
    return list(edges)                        # training range still land somewhere


def apply_numeric_bins(s, edges):
    """Label a series using edges learned on training data."""
    return pd.cut(s, bins=edges, include_lowest=True).astype(str)


def fit_categorical_levels(s, min_frac=0.02):
    """Keep levels holding at least min_frac of the training rows; rest -> OTHER."""
    share = s.value_counts(normalize=True)
    return list(share[share >= min_frac].index)


def apply_categorical_levels(s, levels):
    return np.where(s.isin(levels), s, "OTHER")


# ----------------------------------------------------------------- WoE -----
def woe_table(binned, target, smooth=0.5):
    """
    One row per bin: counts, distributions, WoE and that bin's IV contribution.

    WoE = ln( share of all GOODS in this bin / share of all BADS in this bin )
      positive -> goods over-represented -> lower risk
      negative -> bads  over-represented -> higher risk

    `smooth` adds half a count to each cell so a bin with zero bads (or zero
    goods) gives a large finite WoE instead of infinity.
    """
    d = pd.DataFrame({"bin": binned, "y": target.astype(int)})
    g = d.groupby("bin", dropna=False)["y"].agg(n="size", bad="sum")
    g["good"] = g["n"] - g["bad"]

    g["pct_good"] = (g["good"] + smooth) / (g["good"].sum() + smooth * len(g))
    g["pct_bad"]  = (g["bad"]  + smooth) / (g["bad"].sum()  + smooth * len(g))

    g["bad_rate"] = g["bad"] / g["n"]
    g["woe"]      = np.log(g["pct_good"] / g["pct_bad"])
    g["iv_part"]  = (g["pct_good"] - g["pct_bad"]) * g["woe"]
    return g.reset_index()


def information_value(binned, target, smooth=0.5):
    return woe_table(binned, target, smooth)["iv_part"].sum()


def iv_label(iv):
    if iv < 0.02:  return "useless"
    if iv < 0.10:  return "weak"
    if iv < 0.30:  return "medium"
    if iv < 0.50:  return "strong"
    return "SUSPECT - check for leakage"


def is_monotone(tbl, tol=0.02, ordered=True):
    """
    Does WoE move in one direction across the bins, in bin order?

    Only meaningful for ORDERED bins. For a categorical feature the bin order is
    arbitrary, so the question has no answer and we return None rather than False.

    `tol` forgives reversals smaller than itself. A strict test flags a 0.001 wobble
    between two adjacent bins as non-monotone, which is noise being reported as a
    finding.
    """
    if not ordered:
        return None
    d = np.diff(tbl["woe"].values)
    return bool(np.all(d >= -tol) or np.all(d <= tol))


# --------------------------------------------------------------- driver ----
def fit_all(train, numeric=NUMERIC_FEATURES, categorical=CATEGORICAL_FEATURES,
            target=TARGET, n_bins=5):
    """Learn bins for every feature on the training rows. Returns {feature: rule}."""
    rules = {}
    for f in numeric:
        rules[f] = ("numeric", fit_numeric_bins(train[f], n_bins))
    for f in categorical:
        rules[f] = ("categorical", fit_categorical_levels(train[f]))
    return rules


def transform(df, rules):
    """Apply learned rules, returning a frame of binned (string) columns."""
    out = pd.DataFrame(index=df.index)
    for f, (kind, rule) in rules.items():
        out[f] = (apply_numeric_bins(df[f], rule) if kind == "numeric"
                  else apply_categorical_levels(df[f], rule))
    return out


def iv_summary(train, rules, target=TARGET):
    """IV, bin count and monotonicity for every feature, ranked."""
    binned = transform(train, rules)
    rows = []
    for f in binned.columns:
        t = woe_table(binned[f], train[target])
        iv = t["iv_part"].sum()
        ordered = rules[f][0] == "numeric"
        rows.append({"feature": f, "iv": iv, "strength": iv_label(iv),
                     "bins": len(t), "monotone": is_monotone(t, ordered=ordered)})
    return (pd.DataFrame(rows).sort_values("iv", ascending=False)
              .reset_index(drop=True))
