# Business brief — Olist Marketplace Health & Seller Risk

> **Written 22 September 2026, before any analysis.** Left as it was so the plan can be
> compared with what the evidence actually supported. Four items changed; see
> [What changed, and why](#what-changed-and-why) at the end.

## Context
Olist is a Brazilian marketplace that lets small merchants sell through large online stores, handling
listings, payments and logistics for them. This analysis uses ~99k orders placed between Sep 2016 and
Oct 2018 ([Kaggle public dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)).

**Audience: Head of Marketplace**, who owns growth, seller quality and customer experience.

## Questions this project answers
1. **Is growth healthy?** GMV, orders, items sold, average order value, monthly growth, category mix,
   repeat rate.
   → *Decision: where to focus next — acquiring new customers or retaining existing ones?*
2. **What does late delivery cost us?** Effect of late delivery on review scores and repeat purchase,
   translated into R$ of lost revenue.
   → *Decision: how much is it worth investing in delivery reliability?*
3. **Which sellers are at risk?** A scorecard that flags sellers likely to deliver late or receive poor
   reviews in the next 90 days.
   → *Decision: which sellers to warn, support or review before customers are affected.*
4. **What should we test next?** An A/B test design for an intervention that reduces the damage from
   late delivery.
   → *Decision: which fix to try first, and how long the test must run to give a reliable answer.*

## Early observations from profiling
- **Repeat purchase is rare.** Only 2,997 of 96,096 customers (3.1%) ordered more than once, so growth
  depends almost entirely on new customers.
- **`customer_id` is per order, not per person.** There are 99,441 `customer_id`s but only 96,096 real
  customers; all customer-level analysis uses `customer_unique_id`.
- **The last months of data are incomplete.** Orders run to Oct 2018 but reviews stop at Aug 2018, so
  the analysis window ends before the cut-off to avoid under-counting late deliveries and reviews.

Smaller data-quality issues (duplicate reviews, missing delivery dates, payment mismatches, untranslated
categories) are recorded in [`data_quality_log.md`](data_quality_log.md).

## Out of scope
- **Causal claims.** The data is observational, so results are reported as associations; the A/B test
  design is how causality would be established.
- **Demand forecasting and marketing attribution.** The dataset has no traffic, session or ad-spend data.
- **Pricing and product recommendations.** Separate problems with different data needs.

## Deliverables
- Tested data models (dbt + DuckDB) with a data-quality log
- Metric definitions (`metrics.md`)
- Analysis: growth, cohort retention, customer segments, cost of late delivery
- Seller risk scorecard, validated on later data it was not trained on
- A/B test design with power analysis
- Power BI dashboard (3 pages)
- One-page decision memo
- Live Streamlit app

---

## What changed, and why

Scope that survives contact with the data unchanged usually means the data was never
consulted. Four things moved.

**"Translated into R$ of lost revenue" → not quantified, deliberately.** The plan assumed
late delivery costs money through lost repeat purchase. It does not, in any amount worth
reporting: 97% of customers never return, so there is almost no retention to lose, and
the difference that exists (3.13% on time vs 2.54% late) is worth a few hundred orders
across the whole dataset. Putting a rupee figure on it would have meant inventing a
lifetime-value assumption to carry the whole result. The cost is reported in the unit it
was actually measured in — roughly 3,450 excess one- and two-star reviews.

**"Seller risk scorecard" → a watchlist.** A scorecard was built as far as the panel,
the leakage test and the Weight-of-Evidence screening, then abandoned for a ranked
threshold rule. The reason is in [findings §7](findings.md): an absolute cut scored a
lift of 2.11 in training and 1.12 out of time, because the marketplace late rate tripled
and the rule had learned a fact about 2017 rather than about sellers. A rule that
re-reads the market every month held at 1.51. One feature, no points, no probability —
and it survived the holdout, which the more sophisticated thing did not.

**"Customer segments" → not done, and the reason is in
[findings §2.2](findings.md).** RFM segmentation needs a frequency dimension. With 3.1%
of customers ordering more than once, frequency is 1 for almost everyone, and the
segments would have been an elaborate restatement of recency.

**"Live Streamlit app" and "one-page decision memo" → replaced by a published report.**
The [report site](https://harshit0998.github.io/olist-marketplace-health/) and the Power
BI dashboard cover what both were for, and the project is reproducible from a committed
sample instead — which an app would not have made it.
