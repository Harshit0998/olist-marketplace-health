# Findings — Olist Marketplace Health

Analysis on the `main_marts` models built with dbt + DuckDB. Every figure is reproducible
from `notebooks/01_analysis.ipynb`. Metric definitions are in `metrics.md`; data defects are
in `data_quality_log.md`.

**Analysis window: 2017-01-01 to 2018-08-31 — 20 complete months.**

Sep–Dec 2016 is a pilot period: 4 orders, then 324, then Nov 2016 absent entirely, then 1.
Sep–Oct 2018 is the data collection stopping mid-flight: 20 orders across both months, no
delivery outcomes recorded, and no item rows at all in October. Including either end
produces a chart that appears to show a business collapsing; what it shows is the dataset's
boundary. The window rule is "months where collection is complete" — applied without
reference to whether the numbers look favourable.

---

## 1. Growth stopped five months before the data ends

| | Orders / month |
|---|---|
| Jan 2017 | 800 |
| Mar 2018 | 7,211 — peak |
| Apr 2018 | 6,939 |
| May 2018 | 6,873 |
| Jun 2018 | 6,167 |
| Jul 2018 | 6,292 |
| Aug 2018 | 6,512 |

2017 delivered roughly 9x growth. From March 2018 the business is flat to slightly
declining for five consecutive months, holding around R$1.0–1.15M GMV per month.

**Average order value never moved.** It sits between R$145 and R$175 across the entire
window with no trend. Every rupee of GMV growth came from *more orders*, not larger
baskets — growth is purely an acquisition story.

November 2017 is the single best month at 7,544 orders and R$1.18M — Black Friday.
December falls back to 5,673. The spike did not carry forward.

---

## 2. There is no retention to speak of

**2,997 of 96,096 customers ever placed a second order — 3.1%.**

Monthly, new customers climb from 764 to roughly 7,000 while returning customers rise from
0 to 189 and stay flat against the axis. The business acquires a new cohort every month and
keeps almost none of it.

This single fact governs how everything else should be read: no loyalty base, no
compounding, and effectively no lifetime value beyond the first order.

![Monthly overview](img/monthly_overview.png)

---

## 3. The overall late rate hides a twenty-fold range

The headline is **8.11% of delivered orders arriving after the promised date** — 7,827 of
96,476 orders where the outcome is known. Monthly, that ranges from **1% to 21%**:

| Month | Late rate | Avg review |
|---|---|---|
| Jun 2018 | 1% | 4.28 — highest |
| Jul 2018 | 4% | 4.26 |
| Oct 2017 | 5% | 4.12 |
| Nov 2017 | 14% | 3.91 |
| Feb 2018 | 16% | 3.83 |
| **Mar 2018** | **21%** — worst | **3.75** — lowest |

Review scores track inversely with the late rate across all twenty months.

Note that 8.11% and "a typical month" are different questions. 8.11% correctly answers
*what share of orders were late*. The unweighted mean of the monthly rates is about 10.4%,
inflated by a pilot month with one order, one of them late. **Where the spread is the story,
a single number is a lie of omission** — so the range is reported, not a central value.

Two of the spikes have different characters. November 2017 is Black Friday: a known,
plannable, single-month event. **February and March 2018 are two consecutive months worse
than Black Friday with no seasonal explanation, and they coincide exactly with the point
order growth stalled.** That is an open question this dataset cannot answer.

---

## 4. Late delivery destroys reviews. It does not measurably cost repeat purchases.

### The review effect is very large

| | On time | Late |
|---|---|---|
| Orders | 88,649 | 7,827 |
| Average review score | 4.29 | **2.57** |
| 1–2 star rate | 9% | **54%** |
| 5-star rate | 62% | 22% |
| Average delivery time | 10.8 days | **31.5 days** |

More than half of late orders receive one or two stars, against 9% of on-time orders — six
times the rate. And late orders are not marginally late: 31.5 days against 10.8, so the
customer waited roughly three weeks beyond an already generous estimate.

### The effect scales with how late — and the damage is front-loaded

| Lateness | Orders | Avg review | Change |
|---|---|---|---|
| On time | 89,941 | **4.29** | — |
| 1–3 days late | 1,870 | **3.29** | **−1.00** |
| 4–7 days late | 1,802 | 2.10 | −1.19 |
| 8–14 days late | 1,479 | 1.67 | −0.43 |
| 15+ days late | 1,384 | 1.72 | +0.05 |

**Being merely one to three days late costs a full star.** That is the most actionable
number in this analysis: the intervention should target eliminating small misses, not only
the catastrophic tail. The flattening at 1.67–1.72 is a floor effect — the scale stops at 1,
so further lateness has nowhere left to show.

A monotonic dose-response relationship is meaningfully stronger evidence than a two-group
comparison, because a confounder would have to correlate with the *degree* of lateness
rather than merely its presence.

### The repeat-purchase effect is small and probably immaterial

Taking each customer's **first** order and asking whether they ever returned:

| First order was | Customers | Returned | Repeat rate |
|---|---|---|---|
| On time | 85,662 | 2,683 | **3.13%** |
| Late | 7,592 | 194 | **2.56%** |

A two-proportion z-test gives **z = 2.79, p = 0.0053** — the difference is distinguishable
from chance. But it is 0.6 percentage points in absolute terms against a 3% baseline, and
with 93,254 customers even trivial differences reach significance. **Statistically
detectable, practically negligible.**

### What this means — and it is not the expected answer

The intuitive story is that late delivery angers customers, they do not return, and the cost
is lost future revenue. **The data does not support that chain.** Late delivery makes
customers furious — 54% one or two stars — but they were largely not returning anyway. Only
3% of anyone returns. There is no loyalty to destroy.

**The cost of late delivery therefore cannot be quantified as lost repeat revenue from this
dataset.** It sits elsewhere, and the three plausible channels are:

1. **Acquisition damage.** Late orders produced roughly 4,200 one- and two-star reviews in
   this window, of which about 3,500 are in excess of what the on-time rate would have
   produced. In a business whose only growth engine is new customers, public review scores
   are an acquisition input. Quantifying this needs traffic and conversion data the dataset
   does not contain.
2. **Operational cost.** Support contacts, refunds, disputes, re-shipments. Not in the data.
3. **Seller churn.** The average seller is active only 5.3 of 24 months. Whether late
   delivery predicts a