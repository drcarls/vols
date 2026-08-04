# Instacart milk-price scraper (Bright Data)

Collects milk prices from Instacart across a set of ZIP codes (South Carolina
and comparison areas) and produces normalized price data plus a disparate-impact
summary. Built for use as evidence-gathering in a disproportionate-impact case.

## What it does

1. For every ZIP in `config/zips.csv` × every product in `config/products.csv`,
   it asks Bright Data to return Instacart product/price data for that location.
2. It normalizes everything to one flat CSV schema (`data/milk_prices_*.csv`).
3. `src/analyze.py` compares prices across the demographic **cohorts** you assign
   to each ZIP.

## Two Bright Data strategies

| Strategy   | Bright Data product          | Reliability for Instacart | Env vars needed |
|------------|------------------------------|---------------------------|-----------------|
| `dataset`  | Web Scraper API (Instacart collector) | **High — recommended** | `BRIGHTDATA_API_TOKEN`, `BRIGHTDATA_INSTACART_DATASET_ID` |
| `unlocker` | Web Unlocker                 | Best-effort / DIY parse   | `BRIGHTDATA_API_TOKEN`, `BRIGHTDATA_UNLOCKER_ZONE` |

Instacart is heavily location-gated and JS-rendered, so Bright Data's **managed
Instacart collector** (the `dataset` strategy) is strongly preferred: it handles
the ZIP/location selection and anti-bot layer and returns clean structured rows.
The `unlocker` path is included for completeness but you'll likely need to adapt
the parser in `src/instacart_scraper.py` to Instacart's current markup.

## Setup

```bash
cd milk_price_scraper
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then fill in your Bright Data credentials
```

## Run

```bash
# Recommended path
python scrape.py --strategy dataset

# Smoke-test with a tiny slice first (2 zips x 2 products)
python scrape.py --strategy dataset --max-zips 2 --max-products 2

# Fallback path
python scrape.py --strategy unlocker
```

Output lands in `data/milk_prices_<timestamp>.csv`.

## Analyze

```bash
python src/analyze.py data/milk_prices_*.csv --out data/summary.csv
```

This prints price-by-cohort, a price index vs the cheapest cohort, price-by-ZIP,
and a same-product-across-cohorts table.

## Making the cohorts defensible (South Carolina)

`config/zips.csv` ships with a hand-picked **placeholder** SC set whose
`cohort_label`s end in `_VERIFY`. Before the output carries any evidentiary
weight, regenerate that file from real Census data:

```bash
python src/census_enrich.py                 # -> rewrites config/zips.csv for all of SC
python src/census_enrich.py --min-pop 500   # drop very small ZCTAs
python src/census_enrich.py --cohort income # cohort by income instead of minority share
```

What it does:

- Pulls U.S. Census **ACS 5-year** estimates at the ZCTA level:
  `B03002` (race/ethnicity) and `B19013` (median household income).
- Keeps South Carolina (the only state using ZIP prefixes 290–299, so ZIPs are
  identified by code alone — no fragile crosswalk).
- Computes `minority_pct = (total − non-Hispanic-white-alone) / total` and sorts
  ZIPs into **terciles** for both minority share and income.
- Writes real numbers per ZIP (`total_pop`, `nh_white_pct`, `minority_pct`,
  `median_hh_income`) alongside `minority_tercile`, `income_tercile`, and the
  chosen `cohort_label`.

Keeping the raw demographic numbers in the file means a statistician/expert can
re-cohort or run significance tests however the case requires. **This tooling
produces descriptive evidence, not a legal conclusion** — the significance
testing and interpretation belong to counsel / an expert witness.

> `api.census.gov` must be reachable where you run `census_enrich.py`. Some
> locked-down environments block it (403 at the egress proxy); run it from a
> machine with normal outbound access. `city`/`county` are left blank by the
> generator (not in the ACS ZCTA response); the scraper tolerates blank values,
> and a ZCTA→place crosswalk can fill them later if you want readable labels.

## Legal / compliance note

You are responsible for ensuring your Bright Data plan and use comply with
Instacart's terms and applicable law. This tooling is intended for legitimate
research/evidence-gathering; collect only public pricing data, keep request
volumes reasonable, and retain provenance (timestamps are recorded on every row).
```
