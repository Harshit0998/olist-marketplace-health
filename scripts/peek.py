"""Look at any table in the warehouse.

    python scripts/peek.py                          list every table with row counts
    python scripts/peek.py main_marts.fct_orders    columns, types, and 5 rows
    python scripts/peek.py raw.products 10          10 rows instead of 5
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)

ROOT = Path(__file__).resolve().parents[1]
con = duckdb.connect(str(ROOT / "olist.duckdb"), read_only=True)

if len(sys.argv) == 1:
    rows = con.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema NOT IN ('information_schema')
        ORDER BY 1, 2
    """).fetchall()
    print(f"{'TABLE':<45} {'ROWS':>10}")
    print("-" * 56)
    for schema, name in rows:
        n = con.execute(f"SELECT COUNT(*) FROM {schema}.{name}").fetchone()[0]
        print(f"{schema + '.' + name:<45} {n:>10,}")
else:
    table = sys.argv[1]
    n_rows = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    total = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"\n{table} \u2014 {total:,} rows\n")

    cols = con.execute(f"DESCRIBE {table}").df()
    print(cols[["column_name", "column_type"]].to_string(index=False))

    print(f"\nFirst {n_rows} rows:\n")
    print(con.execute(f"SELECT * FROM {table} LIMIT {n_rows}").df().to_string())

con.close()