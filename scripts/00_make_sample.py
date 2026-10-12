"""
Build a small, referentially consistent sample of the raw Olist data.

Why this exists: the nine Kaggle CSVs are 121 MB and are not committed, so a
fresh clone of this repo cannot build anything and CI has nothing to test
against. This script carves out a slice small enough to commit (about 3.5 MB
gzipped) that still satisfies every foreign key in the project, so
`dbt build` runs end to end on it.

How the slice is chosen: take the N sellers with the most orders, then keep
every order containing an item from one of them, then follow the keys outward -
all items of those orders (including items sold by OTHER sellers, or the order
totals would not reconcile), their payments, reviews, customers, products, and
every seller those items reference. Sampling rows at random instead would break
the relationship tests and leave no seller with enough deliveries for the risk
panel to rank.

The sample is NOT the dataset. Numbers computed from it will not match
docs/findings.md and are not meant to. It exists so the pipeline can be proven
to run, not to reproduce the analysis.

Run from the repo root (needs data/raw/ present):

    python scripts/00_make_sample.py
"""
from pathlib import Path
import duckdb

ROOT    = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "sample"

N_SELLERS  = 10      # top sellers by order count
N_GEO_ROWS = 2000    # geolocation is declared as a source but no model uses it

FILES = {
    "olist_orders_dataset":              "orders",
    "olist_order_items_dataset":         "order_items",
    "olist_order_payments_dataset":      "order_payments",
    "olist_order_reviews_dataset":       "order_reviews",
    "olist_customers_dataset":           "customers",
    "olist_products_dataset":            "products",
    "olist_sellers_dataset":             "sellers",
    "product_category_name_translation": "category_translation",
    "olist_geolocation_dataset":         "geolocation",
}


def src(con, stem):
    """Register one raw CSV as a view so the sampling SQL reads naturally."""
    path = (RAW_DIR / f"{stem}.csv").as_posix()
    con.execute(f"create or replace temp view {FILES[stem]} as "
                f"select * from read_csv_auto('{path}', header = true)")


def main():
    missing = [f"{s}.csv" for s in FILES if not (RAW_DIR / f"{s}.csv").exists()]
    if missing:
        raise SystemExit(f"Missing in {RAW_DIR}:\n  " + "\n  ".join(missing))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()                      # in-memory; nothing is persisted
    for stem in FILES:
        src(con, stem)

    # 1. the seed: the busiest sellers
    con.execute(f"""
        create or replace temp view keep_sellers as
        select seller_id from order_items
        group by seller_id
        order by count(distinct order_id) desc
        limit {N_SELLERS}
    """)

    # 2. every order one of them appears in
    con.execute("""
        create or replace temp view keep_orders as
        select distinct order_id from order_items
        where seller_id in (select seller_id from keep_sellers)
    """)

    # 3. every item on those orders - NOT only the seed sellers' items, or an
    #    order's items would not sum to its payment total
    con.execute("""
        create or replace temp view keep_items as
        select * from order_items where order_id in (select order_id from keep_orders)
    """)

    queries = {
        "olist_orders_dataset":
            "select * from orders where order_id in (select order_id from keep_orders)",
        "olist_order_items_dataset":
            "select * from keep_items",
        "olist_order_payments_dataset":
            "select * from order_payments where order_id in (select order_id from keep_orders)",
        "olist_order_reviews_dataset":
            "select * from order_reviews where order_id in (select order_id from keep_orders)",
        "olist_customers_dataset":
            "select * from customers where customer_id in "
            "(select customer_id from orders where order_id in (select order_id from keep_orders))",
        "olist_products_dataset":
            "select * from products where product_id in (select distinct product_id from keep_items)",
        "olist_sellers_dataset":
            "select * from sellers where seller_id in (select distinct seller_id from keep_items)",
        "product_category_name_translation":
            "select * from category_translation",
        "olist_geolocation_dataset":
            f"select * from geolocation using sample {N_GEO_ROWS} rows",
    }

    print(f"{'file':<38}{'rows':>9}{'KB':>9}")
    print("-" * 56)
    total = 0
    for stem, q in queries.items():
        out = OUT_DIR / f"{stem}.csv.gz"
        con.execute(f"copy ({q}) to '{out.as_posix()}' "
                    f"(format csv, header, compression gzip)")
        n  = con.execute(f"select count(*) from ({q})").fetchone()[0]
        kb = out.stat().st_size / 1024
        total += kb
        print(f"{stem:<38}{n:>9,}{kb:>9,.0f}")

    # the whole point: prove the slice closes over its own foreign keys
    checks = {
        "items reference a kept order":
            "select count(*) from keep_items i left join "
            "(select order_id from orders where order_id in (select order_id from keep_orders)) o "
            "using (order_id) where o.order_id is null",
        "items reference a kept product":
            "select count(*) from keep_items i where i.product_id not in "
            "(select product_id from products where product_id in (select distinct product_id from keep_items))",
        "items reference a kept seller":
            "select count(*) from keep_items i where i.seller_id not in "
            "(select seller_id from sellers where seller_id in (select distinct seller_id from keep_items))",
        "orders reference a kept customer":
            "select count(*) from orders o where o.order_id in (select order_id from keep_orders) "
            "and o.customer_id not in (select customer_id from customers where customer_id in "
            "(select customer_id from orders where order_id in (select order_id from keep_orders)))",
    }
    print("-" * 56)
    print(f"total {total/1024:.1f} MB gzipped\n")
    bad = 0
    for label, q in checks.items():
        n = con.execute(q).fetchone()[0]
        bad += n
        print(f"  {'OK ' if n == 0 else 'FAIL'} {label}" + ("" if n == 0 else f"  ({n} orphans)"))
    con.close()
    if bad:
        raise SystemExit("\nSample is not referentially closed - not safe to commit.")
    print(f"\nwritten to {OUT_DIR}")


if __name__ == "__main__":
    main()
