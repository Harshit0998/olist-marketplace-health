"""Load the 9 raw Olist CSVs into a local DuckDB database (schema: raw).

Run from the repo root:  python scripts/01_load_raw.py
"""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "olist.duckdb"

EXPECTED = {
    "olist_customers_dataset.csv": "customers",
    "olist_geolocation_dataset.csv": "geolocation",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_orders_dataset.csv": "orders",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "product_category_name_translation.csv": "category_translation",
}

missing = [f for f in EXPECTED if not (RAW_DIR / f).exists()]
if missing:
    raise SystemExit(f"Missing files in {RAW_DIR}:\n  " + "\n  ".join(missing))

con = duckdb.connect(str(DB_PATH))
con.execute("CREATE SCHEMA IF NOT EXISTS raw")

for file_name, table in EXPECTED.items():
    path = (RAW_DIR / file_name).as_posix()
    con.execute(f"""
        CREATE OR REPLACE TABLE raw.{table} AS
        SELECT * FROM read_csv_auto('{path}', header = true)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM raw.{table}").fetchone()[0]
    print(f"raw.{table:<22} {n:>9,} rows")

con.close()
print(f"\nLoaded into {DB_PATH.name}")
