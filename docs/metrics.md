# Metric definitions

One definition per metric. The dashboard, the models and the memo all use these. If a number
anywhere disagrees with this file, this file wins — or the file gets changed deliberately,
not the number quietly.

All money is in Brazilian reais (R$). Source of truth for revenue is `main_marts.fct_orders`.

## Analysis window

**2017-01-01 to 2018-08-31 — 20 complete months.**

Applied to every trend, rate and cohort figure, and stated wherever a number is quoted.
The rule is "months where data collection is complete", which excludes Sep–Dec 2016 (pilot:
4, 324, absent, 1 orders) and Sep–Oct 2018 (collection stopping: 20 orders, no delivery
outcomes, no item rows in October). The rule is independent of whether the excluded months
look favourable.

**The window is not applied inside the marts models.** A mart exposes what the data
contains; the analysis decides what to show. `fct_monthly` therefore has 25 rows, and
`n_reviews` is the column that makes the incompleteness visible to anyone reading it.

---

## Volume and value

### GMV
**Total value of goods sold, including freight.**
`sum(order_revenue)` from `fct_orders`, where `order_revenue = sum(price + freight_value)`
over the order's item lines.

- **Full-period value: R$ 15,843,553.24**, reconciling across `fct_orders`,
  `dim_customers` and `fct_seller_monthly`.
- **Decision — GMV includes freight.** Some companies define GMV as goods only. Ours
  includes it because freight is money the marketplace moves.
- **Decision — GMV comes from `order_items`, not `order_payments`.** The two disagree on
  249 orders (0.25%), consistent with instalment interest or vouchers. Payments are used
  only for payment-method analysis.
- NULL for orders with no item rows; `sum` skips them.

### Orders
`count(distinct order_id)` from `fct_orders`. **99,441** over the full dataset. Includes
every status — cancelled and unavailable orders are counted unless a filter says otherwise.

### Items
`sum(n_items)` from `fct_orders` — item *lines*, not distinct products. An order with 3
copies of one book is 3 items and 1 product.

### Average order value (AOV)
`sum(order_revenue) / count(distinct order_id)`.
**About R$ 159 overall; R$145–175 monthly with no trend.**

Computed as a **ratio of totals**, never as `avg(order_revenue)` — the second treats a R$20
order and a R$2,000 order as equally important.

---

## Customers

### Customers
`count(distinct customer_unique_id)` from `dim_customers`. **96,096.**
**Never `customer_id`**, which is issued per order — 99,441 of them exist, which would
overstate the customer base by 3.5%.

### New customers (per month)
`count(*)` over `dim_customers`, grouped by `date_trunc('month', first_order_at)`.
A person is new exactly once, so this column sums to 96,096 across all months.

### Returning customers (per month)
`n_customers - n_new_customers` within `fct_monthly`: people active in that month who were
not first-timers in it. Note this is *active and not new*, not *active in consecutive months*.

### Repeat rate
`count(*) filter (where is_repeat) / count(*)` over `dim_customers`, where
`is_repeat = n_orders > 1`. **2,997 / 96,096 = 3.1%.**

### Lifetime revenue
`sum(order_revenue)` per `customer_unique_id`. NULL when the person's only order had no
item rows.

---

## Delivery

### Delivery days
`date_diff('day', purchased_at, delivered_at)`.
**Counts calendar-day boundaries crossed, not 24-hour periods** — an order placed at 23:00
and delivered at 01:00 next day counts as 1 day. Cannot answer "delivered within 24 hours".

### Delay days
`date_diff('day', estimated_delivery_at, delivered_at)`.
**Positive = late, negative = early, zero = arrived on the promised day.**

### is_late
`date_diff('day', order_estimated_delivery_date, order_delivered_customer_date) > 0`.

**An order is late when it arrives on a later calendar day than promised.** The promise made
to the customer is a date, not a timestamp, so a parcel arriving at any hour on the promised
day is on time.

This was previously `delivered_at > estimated_delivery_at`, which counted 1,292 same-day
deliveries as late because the estimate is a date (midnight). See finding 12 in
`data_quality_log.md`. The change moved the late rate from 8.11% to 6.77%.

**NULL when the order has no delivery date** (not delivered, or one of the 8 delivered
orders with a missing date). NULL means unknown, never on time.

### Late rate (overall) — the headline number
`count(*) filter (where is_late) / count(is_late)` over `fct_orders`.
**6,535 / 96,476 = 6.77%.**

The denominator is `count(is_late)`, which excludes NULLs — measured only over orders where
the answer is known. Monthly it ranges from 1% to 19%.

### Late rate (seller average)
`avg(late_rate)` over `dim_sellers`. **6.91%.**

**A different number that must never be quoted as the late rate.** It weights every seller
equally regardless of volume. The 0.14-point gap against the order-weighted figure is
consistent with smaller sellers performing marginally worse, but it is small.

> Rule: rates cannot be averaged. To combine periods or sellers, sum the numerators and
> denominators and divide once.

---

## Reviews

### Average review score
`avg(review_score)` over orders that have a review. Scale is 1–5.

### Review coverage
`count(*) filter (where has_review) / count(*)` over `fct_orders`. Reviews stop in Aug 2018
while orders run to Oct 2018 — another reason for the window.

### Low review rate
`count(*) filter (where review_score <= 2) / count(review_score)`.
1 and 2 stars count as low; 3 is neutral and excluded.

---

## Sellers

### Sellers
`count(distinct seller_id)` from `dim_sellers`. **3,095.**

### Active months per seller
Rows in `fct_seller_monthly` ÷ distinct sellers. **16,441 / 3,095 = 5.3 months** of 24.
Most sellers have short tenure, which limits how much history the risk scorecard can use.

### Seller late rate (monthly)
`n_late / nullif(n_late_known, 0)` within a (seller, month) row. NULL when the seller had no
delivered orders that month. Both counts are stored so months can be combined correctly.

---

## Conventions

- Every rate uses `nullif(denominator, 0)`.
- Every division multiplies by `1.0` to avoid integer division.
- A seller/month with no sales produces **no row** in `fct_seller_monthly`; a month with no
  orders produces no row in `fct_monthly` (Nov 2016). Downstream code must treat a missing
  period as zero activity, not missing data.
- An order with several sellers counts as late for **each** seller on it, so seller-level
  denominators do not sum to the order count.