"""Profile every raw table and write docs/data_profile.md.

Part 1 (automatic): row count + per-column type, nulls, distinct values, min, max.
Part 2 (you write): targeted checks on keys and business rules -> CHECKS below.

Run from the repo root:  python scripts/02_profile.py
"""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "olist.duckdb"
OUT = ROOT / "docs" / "data_profile.md"
OUT.parent.mkdir(exist_ok=True)

con = duckdb.connect(str(DB_PATH), read_only=True)
tables = [r[0] for r in con.execute(
    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'raw' ORDER BY 1"
).fetchall()]

lines = ["# Data profile — raw Olist tables", ""]

for t in tables:
    n = con.execute(f"SELECT COUNT(*) FROM raw.{t}").fetchone()[0]
    s = con.execute(f"SUMMARIZE raw.{t}").df()
    s = s[["column_name", "column_type", "null_percentage", "approx_unique", "min", "max"]]
    lines += [f"## raw.{t} — {n:,} rows", "", s.to_markdown(index=False), ""]

# ---------------------------------------------------------------------------
# Part 2 — YOUR checks. Each query should return ONE number; 0 usually = clean.
# Write the SQL yourself. Examples of what to test are in the comments.
# ---------------------------------------------------------------------------
CHECKS = {
    "1 orders: duplicate order_id": "SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM raw.orders",
    "2 customers: distinct customer_id vs distinct customer_unique_id" : "SELECT COUNT(distinct customer_id) - COUNT(distinct customer_unique_id) FROM raw.customers",
    "3 customers: people with more than one order": 
        """
        SELECT COUNT(*) FROM (
            SELECT c.customer_unique_id
            FROM raw.orders o
            JOIN raw.customers c ON c.customer_id = o.customer_id
            GROUP BY c.customer_unique_id
            HAVING COUNT(*) > 1
        )""",
    "4 order_items: orphan rows (order not in orders)": """
        SELECT COUNT(*) FROM raw.order_items oi
        WHERE NOT EXISTS (SELECT 1 FROM raw.orders o WHERE o.order_id = oi.order_id)
    """,
    "5 reviews: duplicate review_id" : "SELECT COUNT(*) - COUNT(DISTINCT review_id) FROM raw.order_reviews",
    "6 orders with more than one review": """
        SELECT COUNT(*) FROM (
            SELECT order_id FROM raw.order_reviews
            GROUP BY order_id
            HAVING COUNT(review_id) > 1
        )
    """,
    "7 delivered orders with no delivery date": """
        SELECT COUNT(*) FROM raw.orders
        WHERE order_status = 'delivered' AND order_delivered_customer_date IS NULL
    """,
    "8 delivered before purchased": """
        SELECT COUNT(*) FROM raw.orders
        WHERE order_delivered_customer_date < order_purchase_timestamp
    """,
    "9 products whose category has no English name": """
        SELECT COUNT(DISTINCT p.product_category_name) FROM raw.products p
        WHERE p.product_category_name IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM raw.category_translation t
                          WHERE t.product_category_name = p.product_category_name)
    """,
    "10 orders where payments differ from items + freight by more than 1" : """
        WITH items AS (
            SELECT order_id, SUM(price + freight_value) AS item_total
            FROM raw.order_items GROUP BY order_id
        ),
        pays AS (
            SELECT order_id, SUM(payment_value) AS pay_total
            FROM raw.order_payments GROUP BY order_id
        )
        SELECT COUNT(*) FROM items i JOIN pays p ON p.order_id = i.order_id
        WHERE ABS(i.item_total - p.pay_total) > 1
    """
}

if CHECKS:
    lines += ["## Targeted checks", "", "| Check | Result |", "|---|---|"]
    for name, sql in CHECKS.items():
        val = con.execute(sql).fetchone()[0]
        lines.append(f"| {name} | {val:,} |")
        print(f"{name:<60} {val:>10,}")

con.close()
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nWrote {OUT.relative_to(ROOT)}")
