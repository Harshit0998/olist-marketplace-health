"""
Export the marts Power BI needs, as CSV.

Run after `dbt build`. Writes to data/bi/, which is gitignored: these files are
derived, and this script plus the dbt models are what the repo actually keeps.
The .pbix imports the data, so it opens standalone without them.

    python scripts/03_export_bi.py
"""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB   = ROOT / "olist.duckdb"
OUT  = ROOT / "data" / "bi"

TABLES = [
    # page 1 - marketplace health
    "main_marts.fct_monthly",
    "main_marts.fct_cohort_retention",
    # page 2 - delivery and experience
    "main_marts.fct_delivery_by_state",
    "main_marts.fct_delivery_by_category",
    "main_marts.fct_delay_bands",
    # page 3 - sellers
    "main_marts.dim_sellers",
    "main_marts.fct_seller_monthly",
    "main_marts.fct_seller_snapshots",
]

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB), read_only=True)
    print(f"{'table':<34}{'rows':>9}{'KB':>8}")
    print("-" * 51)
    for t in TABLES:
        name = t.split(".")[-1]
        path = OUT / f"{name}.csv"
        # COPY writes straight from DuckDB - no pandas round trip, UTF-8 by default
        con.execute(f"copy (select * from {t}) to '{path.as_posix()}' "
                    f"(header, delimiter ',')")
        n = con.execute(f"select count(*) from {t}").fetchone()[0]
        print(f"{name:<34}{n:>9,}{path.stat().st_size // 1024:>8,}")
    con.close()
    print("-" * 51)
    print(f"written to {OUT}")

if __name__ == "__main__":
    main()
