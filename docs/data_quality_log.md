\# Data-quality log



Every issue found while profiling the raw Olist tables, what it costs, and how it is

handled. Numbers come from `scripts/02\_profile.py`; the automated versions of these

checks live in `olist\_dbt/models/staging/sources.yml` and `olist\_dbt/models/staging/schema.yml`.



Status key: \*\*Fixed\*\* = corrected in a staging model · \*\*Accepted\*\* = real, documented,

not corrected · \*\*Clean\*\* = checked, nothing found.



| # | Issue | Evidence | Why it matters | Handling | Status |

|---|---|---|---|---|---|

| 1 | `customer\_id` is per order, not per person | 99,441 `customer\_id` vs 96,096 `customer\_unique\_id` (3,345 difference) | Counting customers by `customer\_id` overstates them by 3.5% and makes repeat purchase invisible | All customer-level work keys on `customer\_unique\_id`; `dim\_customers` is built at person grain | Accepted |

| 2 | `review\_id` is not unique | 814 duplicate rows in 99,224 | A join on reviews would fan out and double-count revenue | `stg\_order\_reviews` keeps the most recent review per order via `ROW\_NUMBER()`; 99,224 → 98,673 rows. The `unique` test on `order\_id` proves it | Fixed |

| 3 | Orders with more than one review | 547 orders | Same fan-out risk; also makes the review score per order ambiguous | Most recent review wins (see #2) | Fixed |

| 4 | Delivered orders with no delivery date | 8 orders | Late/on-time cannot be computed for these; treating them as on-time would understate the late rate | `is\_late` is NULL when the delivery date is missing; late rate is measured only over the 96,476 delivered orders that have a date | Accepted |

| 5 | Payments ≠ items + freight | 249 orders (0.25%), difference > R$1 | GMV differs depending on which table you sum | GMV is defined from `order\_items` (`price + freight\_value`); payments are used only for payment-type analysis. The gap is consistent with instalment interest or voucher use, but this has not been verified against a payments specification | Accepted |

| 6 | Categories with no English translation | 2 categories | Category charts would mix Portuguese names in among English ones | `stg\_products` falls back to the Portuguese name via `coalesce` | Fixed |

| 7 | Products with no category at all | 610 products | These drop out of any category breakdown | Left as NULL and reported as "Uncategorised" rather than dropped, so category totals still reconcile to the overall total | Accepted |

| 8 | Reviews stop before orders do | Orders run to Oct 2018, reviews to Aug 2018 | The final weeks look artificially review-free and artificially on-time | The analysis window ends \*\*2018-08-31\*\*; orders after that date are excluded from trend, review and late-rate metrics | Accepted |

| 9 | Duplicate `order\_id` in orders | 0 | — | `unique` + `not\_null` tests enforce it | Clean |

| 10 | Orphan `order\_items` (order not in orders) | 0 | — | `relationships` test enforces it | Clean |

| 11 | Delivered before purchased | 0 | — | Checked; no negative delivery times | Clean |



\## What became an automated test, and what did not



A test encodes a rule that must \*\*always\*\* hold. A known, accepted gap is a documented

finding, not a failing test — a pipeline that is permanently red is a pipeline everyone

stops reading.



\*\*Enforced\*\* — 24 tests on the raw sources, 27 on the staging models:



\- `unique` + `not\_null` on every primary key

\- `relationships` on every foreign key (`order\_items` → orders, products, sellers;

&#x20; `order\_payments` → orders)

\- `accepted\_values` on `review\_score`, restricted to 1–5

\- `unique` on `stg\_order\_reviews.order\_id`, which is the proof that the deduplication

&#x20; in #2 worked



\*\*Not enforced, documented instead\*\* — #2 (`review\_id` uniqueness), #4 (missing

delivery dates), #5 (payment mismatch), #7 (missing categories). Each is written into

the relevant model's `description:` in `schema.yml`, so the next person reading the

project finds it without rerunning the profiling script.



\## How to reproduce



```

python scripts/02\_profile.py          # regenerates docs/data\_profile.md and the 11 checks

cd olist\_dbt

dbt build --profiles-dir .            # builds 8 models, runs 51 tests

```

