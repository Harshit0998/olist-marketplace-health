# Olist Marketplace Health & Seller Risk

> Work in progress (Sep–Oct 2026). Findings will lead this README once the analysis is done.

End-to-end analytics project on the Olist Brazilian e-commerce dataset (~100k orders, 2016–2018):
tested data models, marketplace KPIs, cohort retention, the cost of late delivery, a seller risk
scorecard, an A/B test design, a Power BI dashboard and a live Streamlit app.

## Reproduce
1. Download the dataset from https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce and unzip the 9 CSVs into `data/raw/`.
2. `pip install -r requirements.txt`
3. `python scripts/01_load_raw.py`
4. `python scripts/02_profile.py`
