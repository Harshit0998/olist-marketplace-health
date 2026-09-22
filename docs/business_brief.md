# Business brief — Olist Marketplace Health & Seller Risk

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
