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
    # "orders: duplicate order_id": "SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM raw.orders",
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
