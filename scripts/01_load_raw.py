"""Load the nine raw Olist CSVs into a local DuckDB database (schema: raw).

Two sources:

    python scripts/01_load_raw.py             # data/raw/     the real 121 MB Kaggle files
    python scripts/01_load_raw.py --sample    # data/sample/  the committed 3.5 MB slice

The sample is what CI builds against, because the Kaggle files are not in the
repo. It is a real subset - every foreign key closes - but it is only ten
sellers, so numbers computed from it do not match docs/findings.md and are not
meant to. See scripts/00_make_sample.py.
"""
import argparse
from pathlib import Path
import duckdb

ROOT    = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "olist.duckdb"

EXPECTED = {
    "olist_customers_dataset":           "customers",
    "olist_geolocation_dataset":         "geolocation",
    "olist_order_items_dataset":         "order_items",
    "olist_order_payments_dataset":      "order_payments",
    "olist_order_reviews_dataset":       "order_reviews",
    "olist_orders_dataset":              "orders",
    "olist_products_dataset":            "products",
    "olist_sellers_dataset":             "sellers",
    "product_category_name_translation": "category_translation",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", action="store_true",
                    help="load the committed sample instead of data/raw/")
    ap.add_argument("--db", default=str(DB_PATH), help="target DuckDB file")
    args = ap.parse_args()

    # DuckDB's read_csv_auto decompresses .gz transparently, so the only
    # difference between the two sources is the directory and the extension.
    src_dir = ROOT / "data" / ("sample" if args.sample else "raw")
    suffix  = ".csv.gz" if args.sample else ".csv"

    missing = [s + suffix for s in EXPECTED if not (src_dir / (s + suffix)).exists()]
    if missing:
        hint = ("\n\nRun scripts/00_make_sample.py to build it."
                if args.sample else
                "\n\nDownload the Olist dataset from Kaggle into data/raw/,"
                "\nor use --sample to build from the committed slice.")
        raise SystemExit(f"Missing in {src_dir}:\n  " + "\n  ".join(missing) + hint)

    con = duckdb.connect(args.db)
    con.execute("create schema if not exists raw")

    print(f"source: {src_dir.relative_to(ROOT)}{'  (SAMPLE - not the full dataset)' if args.sample else ''}\n")
    for stem, table in EXPECTED.items():
        path = (src_dir / (stem + suffix)).as_posix()
        con.execute(f"""
            create or replace table raw.{table} as
            select * from read_csv_auto('{path}', header = true)
        """)
        n = con.execute(f"select count(*) from raw.{table}").fetchone()[0]
        print(f"raw.{table:<22} {n:>9,} rows")

    con.close()
    print(f"\nloaded into {Path(args.db).name}")


if __name__ == "__main__":
    main()
