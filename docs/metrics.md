\# Metric definitions



One definition per metric. The dashboard, the models and the memo all use these.

If a number anywhere disagrees with this file, this file wins — or the file gets

changed deliberately, not the number quietly.



All money is in Brazilian reais (R$). Source of truth for revenue is

`main\_marts.fct\_orders`; the analysis window ends 2018-08-31 (see

`data\_quality\_log.md`, finding 8).



\---



\## Volume and value



\### GMV

\*\*Total value of goods sold, including freight.\*\*

`sum(order\_revenue)` from `fct\_orders`, where `order\_revenue = sum(price + freight\_value)`

over the order's item lines.



\- \*\*Full-period value: R$ 15,843,553.24\*\*

\- \*\*Decision — GMV includes freight.\*\* Some companies define GMV as goods only.

&#x20; Ours includes it because freight is money the marketplace moves.

\- \*\*Decision — GMV comes from `order\_items`, not `order\_payments`.\*\* The two disagree

&#x20; on 249 orders (0.25%), consistent with instalment interest or vouchers. Payments are

&#x20; used only for payment-method analysis.

\- NULL for orders with no item rows; `sum` skips them.



\### Orders

`count(distinct order\_id)` from `fct\_orders`. \*\*99,441\*\* over the full period.

Includes every status — cancelled and unavailable orders are counted unless a

filter says otherwise.



\### Items

`sum(n\_items)` from `fct\_orders` — item \*lines\*, not distinct products.

An order with 3 copies of one book is 3 items and 1 product.



\### Average order value (AOV)

`sum(order\_revenue) / count(distinct order\_id)`.

Computed as a \*\*ratio of totals\*\*, never as `avg(order\_revenue)`.



\---



\## Customers



\### Customers

`count(distinct customer\_unique\_id)` from `dim\_customers`. \*\*96,096.\*\*

\*\*Never `customer\_id`\*\*, which is issued per order — 99,441 of them exist, which would

overstate the customer base by 3.5%.



\### Repeat rate

`count(\*) filter (where is\_repeat) / count(\*)` over `dim\_customers`,

where `is\_repeat = n\_orders > 1`.

\*\*2,997 / 96,096 = 3.1%.\*\*



\### Lifetime revenue

`sum(order\_revenue)` per `customer\_unique\_id`. NULL when the person's only order

had no item rows.



\---



\## Delivery



\### Delivery days

`date\_diff('day', purchased\_at, delivered\_at)`.

\*\*Counts calendar-day boundaries crossed, not 24-hour periods\*\* — an order placed

at 23:00 and delivered at 01:00 next day counts as 1 day. Cannot answer

"delivered within 24 hours."



\### Delay days

`date\_diff('day', estimated\_delivery\_at, delivered\_at)`.

\*\*Positive = late, negative = early.\*\*



\### is\_late

`delivered\_at > estimated\_delivery\_at`.

\*\*NULL when the order has no delivery date\*\* (not delivered, or one of the 8

delivered orders with a missing date). NULL is "unknown", never "on time".



\### Late rate (overall) — the headline number

`count(\*) filter (where is\_late) / count(is\_late)` over `fct\_orders`.

\*\*7,827 / 96,476 = 8.11%.\*\*

The denominator is `count(is\_late)`, which excludes NULLs — measured only over

orders where the answer is known.



\### Late rate (seller average)

`avg(late\_rate)` over `dim\_sellers`. \*\*8.42%.\*\*

\*\*This is a different number and must never be quoted as the late rate.\*\* It weights

every seller equally regardless of volume, so small sellers dominate. The gap between

8.42% and 8.11% is itself a finding: small sellers deliver worse.



> Rule: rates cannot be averaged. To combine periods or sellers, sum the numerators

> and denominators and divide once.



\---



\## Reviews



\### Average review score

`avg(review\_score)` over orders that have a review. Scale is 1–5.



\### Review coverage

`count(\*) filter (where has\_review) / count(\*)` over `fct\_orders`.

Reviews stop in Aug 2018 while orders run to Oct 2018, so coverage collapses at the

end of the raw data — another reason for the 2018-08-31 window.



\### Low review rate

`count(\*) filter (where review\_score <= 2) / count(review\_score)`.

1 and 2 stars count as low; 3 is neutral and excluded.



\---



\## Sellers



\### Sellers

`count(distinct seller\_id)` from `dim\_sellers`. \*\*3,095.\*\*



\### Active months per seller

Rows in `fct\_seller\_monthly` ÷ distinct sellers. \*\*16,441 / 3,095 = 5.3 months\*\*

out of 24. Most sellers have short tenure, which limits how much history the risk

scorecard can use.



\### Seller late rate (monthly)

`n\_late / nullif(n\_late\_known, 0)` within a (seller, month) row.

NULL when the seller had no delivered orders that month. `n\_late` and `n\_late\_known`

are both stored so months can be combined correctly.



\---



\## Conventions



\- Every rate uses `nullif(denominator, 0)`.

\- Every division multiplies by `1.0` to avoid integer division.

\- A seller/month with no sales produces \*\*no row\*\* in `fct\_seller\_monthly`.

&#x20; Downstream code must treat a missing month as zero sales, not missing data.

\- An order with several sellers counts as late for \*\*each\*\* seller on it, so

&#x20; seller-level denominators do not sum to the order count.

