#!/usr/bin/env python3
"""Generate a demographically-grounded South Carolina ZIP table from Census ACS.

Why this exists
---------------
For a disparate-impact argument, the cohort each ZIP belongs to must come from
real demographic data, not assumptions. This script pulls American Community
Survey (ACS) 5-year estimates at the ZCTA (ZIP-code-tabulation-area) level,
keeps South Carolina, computes each ZIP's minority share and median household
income, sorts ZIPs into terciles, and writes `config/zips.csv`.

South Carolina is the only state using ZIP prefixes 290-299, so we can identify
SC ZCTAs by the 5-digit code alone (^29\\d{3}$) -- no fragile state crosswalk.

ACS variables used
------------------
  B03002_001E  total population
  B03002_003E  Not Hispanic or Latino: White alone
  B19013_001E  median household income (USD)

  minority_pct = (total - non-Hispanic white alone) / total * 100

Cohorts
-------
  minority_tercile : low_minority / mid_minority / high_minority  (by minority_pct)
  income_tercile   : lower_income / middle_income / higher_income  (by median income)
  cohort_label     : defaults to minority_tercile (the usual primary axis for a
                     race-based disparate-impact analysis); override with --cohort.

The raw numbers are kept in the output so a statistician/expert can re-cohort or
run significance tests however the case requires. This script only labels; it
does not itself establish legal disparate impact.

Usage
-----
  python src/census_enrich.py                       # latest supported year -> config/zips.csv
  python src/census_enrich.py --year 2022 --min-pop 500
  python src/census_enrich.py --api-key $CENSUS_API_KEY   # optional; higher rate limits

Note: api.census.gov must be reachable from wherever you run this. In a locked-down
egress environment it may be blocked (403 at the proxy) -- run it somewhere with
outbound access to that host.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import pandas as pd
    import requests
except ImportError:
    print("This script needs pandas and requests: pip install -r requirements.txt",
          file=sys.stderr)
    raise

HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE.parent / "config" / "zips.csv"

ACS_VARS = {
    "B03002_001E": "total_pop",
    "B03002_003E": "nh_white",
    "B19013_001E": "median_hh_income",
}
# Census uses large negative sentinels (e.g. -666666666) for "not available".
NULL_SENTINEL_MAX = -1_000_000

OUTPUT_COLUMNS = [
    "zip", "city", "county", "region",
    "total_pop", "nh_white_pct", "minority_pct", "median_hh_income",
    "minority_tercile", "income_tercile", "cohort_label",
]


def acs_url(year: int) -> str:
    return f"https://api.census.gov/data/{year}/acs/acs5"


def fetch_acs(year: int, api_key: str | None, timeout: int = 120) -> list[list[str]]:
    """Return the raw ACS response (header row + data rows) for all ZCTAs."""
    params = {
        "get": "NAME," + ",".join(ACS_VARS.keys()),
        "for": "zip code tabulation area:*",
    }
    if api_key:
        params["key"] = api_key
    resp = requests.get(acs_url(year), params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def build_zip_table(
    raw: list[list[str]],
    min_pop: int = 100,
    cohort: str = "minority",
) -> "pd.DataFrame":
    """Pure transform: ACS rows -> tidy SC ZIP table. Testable without network."""
    header, *rows = raw
    df = pd.DataFrame(rows, columns=header)

    # The ZCTA code is the last column; its header name varies by vintage.
    zcta_col = "zip code tabulation area"
    if zcta_col not in df.columns:
        zcta_col = df.columns[-1]
    df = df.rename(columns={zcta_col: "zip", **ACS_VARS})

    # South Carolina = ZIP prefixes 290-299.
    df = df[df["zip"].str.match(r"^29\d{3}$", na=False)].copy()

    for col in ("total_pop", "nh_white", "median_hh_income"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.loc[df["median_hh_income"] < NULL_SENTINEL_MAX, "median_hh_income"] = pd.NA

    df = df[df["total_pop"].fillna(0) >= min_pop].copy()
    df = df[df["total_pop"] > 0].copy()

    df["minority_pct"] = ((df["total_pop"] - df["nh_white"]) / df["total_pop"] * 100).round(1)
    df["nh_white_pct"] = (df["nh_white"] / df["total_pop"] * 100).round(1)

    df["minority_tercile"] = _tercile(
        df["minority_pct"], ["low_minority", "mid_minority", "high_minority"]
    )
    df["income_tercile"] = _tercile(
        df["median_hh_income"], ["lower_income", "middle_income", "higher_income"]
    )

    df["cohort_label"] = (
        df["income_tercile"] if cohort == "income" else df["minority_tercile"]
    )

    # City/county/region aren't in the ACS ZCTA response; leave for optional manual
    # or crosswalk enrichment. The scraper tolerates blank values.
    for col in ("city", "county", "region"):
        df[col] = ""

    df["total_pop"] = df["total_pop"].astype("Int64")
    df["median_hh_income"] = df["median_hh_income"].astype("Int64")
    return df[OUTPUT_COLUMNS].sort_values("zip").reset_index(drop=True)


def _tercile(series: "pd.Series", labels: list[str]) -> "pd.Series":
    """Assign terciles; robust to ties/NaN (NaN -> empty label)."""
    valid = series.dropna()
    if valid.nunique() < 3:
        # Not enough spread to form 3 buckets; bail to a single middle label.
        return series.apply(lambda v: labels[1] if pd.notna(v) else "")
    try:
        cut = pd.qcut(series, 3, labels=labels, duplicates="drop")
    except ValueError:
        return series.apply(lambda v: labels[1] if pd.notna(v) else "")
    return cut.astype("object").fillna("")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--year", type=int, default=2022,
                        help="ACS 5-year vintage (default 2022).")
    parser.add_argument("--min-pop", type=int, default=100,
                        help="Drop ZIPs below this population (default 100).")
    parser.add_argument("--cohort", choices=["minority", "income"], default="minority",
                        help="Which axis becomes cohort_label (default minority).")
    parser.add_argument("--api-key", default=None, help="Optional Census API key.")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    print(f"Fetching ACS {args.year} 5-year ZCTA data from api.census.gov ...")
    try:
        raw = fetch_acs(args.year, args.api_key)
    except requests.exceptions.RequestException as exc:
        print(f"\nCensus API request failed: {exc}", file=sys.stderr)
        print("If this is a 403/blocked host, run this script somewhere with "
              "outbound access to api.census.gov.", file=sys.stderr)
        return 1

    df = build_zip_table(raw, min_pop=args.min_pop, cohort=args.cohort)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    print(f"Wrote {len(df)} South Carolina ZIPs -> {out_path}")
    counts = df["cohort_label"].value_counts()
    print("\nCohort sizes:")
    print(counts.to_string())
    print("\nMedian income by cohort:")
    print(df.groupby("cohort_label")["median_hh_income"].median().round(0).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
