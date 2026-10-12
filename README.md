# Olist Marketplace Health & Seller Risk

[![dbt build](https://github.com/Harshit0998/olist-marketplace-health/actions/workflows/ci.yml/badge.svg)](https://github.com/Harshit0998/olist-marketplace-health/actions/workflows/ci.yml)

> Work in progress (Sep–Oct 2026). Findings will lead this README once the analysis is done.

End-to-end analytics on the Olist Brazilian e-commerce dataset (99,441 orders, 2016–2018):
tested data models in dbt + DuckDB, marketplace KPIs, cohort retention, the cost of late
delivery, a monthly seller risk watchlist, and a three-page Power BI dashboard.

**19 models · 123 tests · every push rebuilt and tested by CI.**

See [`docs/findings.md`](docs/findings.md) for the analysis.

## Reproduce

The project builds two ways. The sample needs nothing but this repository.

**From the committed sample** (3.5 MB, ten sellers — proves the pipeline, does not
reproduce the numbers in `docs/findings.md`):

```bash
pip install -r requirements-ci.txt
python scripts/01_load_raw.py --sample --db olist_ci.duckdb
cd olist_dbt && dbt deps && dbt build --target ci
```

**From the full dataset:**

1. Download from [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
   and unzip the nine CSVs into `data/raw/`
2. `pip install -r requirements.txt`
3. `python scripts/01_load_raw.py`
4. `python scripts/02_profile.py`
5. `cd olist_dbt && dbt deps && dbt build`

## Layout

| Path | What it is |
|---|---|
| `olist_dbt/models/staging/` | 8 views: light cleaning, one per source table |
| `olist_dbt/models/marts/` | 11 tables: the business-ready models |
| `olist_dbt/tests/` | Singular tests that generic ones cannot express |
| `scripts/` | Load, profile, sample, BI export, watchlist evaluation |
| `docs/` | Findings, metrics definitions, data-quality log, dashboard images |
| `powerbi/` | `.pbix`, `.pbit` and an exported PDF of the dashboard |

Data under `data/raw/` and `data/bi/` is not committed; `data/sample/` is.

## Credit

Dataset: [Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce),
published by Olist under CC BY-NC-SA 4.0. The sample under `data/sample/` is a subset of it.
