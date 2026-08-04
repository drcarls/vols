#!/usr/bin/env python3
"""Disparate-impact analysis of scraped Instacart milk prices.

Reads one or more scraped CSVs (from scrape.py) and produces summary tables
comparing milk prices across the `cohort_label` you assign to each ZIP.

This is deliberately conservative: it reports observed price differences and
simple group statistics. It does NOT, by itself, establish legal disparate
impact -- that requires (a) demographically validated cohort definitions, ideally
from Census ACS data joined on ZIP, and (b) proper statistical testing and
expert interpretation. Treat the output as descriptive evidence to hand to
counsel / an expert witness, not as a conclusion.

Usage:
  python src/analyze.py data/milk_prices_*.csv
  python src/analyze.py data/milk_prices_*.csv --out data/summary.csv
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("pandas is required for analysis: pip install pandas", file=sys.stderr)
    raise


def load_frames(patterns: list[str]) -> "pd.DataFrame":
    paths: list[str] = []
    for pat in patterns:
        paths.extend(glob.glob(pat))
    if not paths:
        raise SystemExit(f"No files matched: {patterns}")
    frames = [pd.read_csv(p) for p in paths]
    df = pd.concat(frames, ignore_index=True)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["price"])
    df = df[df["price"] > 0]
    return df


def summarize(df: "pd.DataFrame") -> dict[str, "pd.DataFrame"]:
    out: dict[str, pd.DataFrame] = {}

    # Price by cohort.
    if "cohort_label" in df and df["cohort_label"].notna().any():
        by_cohort = (
            df.groupby("cohort_label")["price"]
            .agg(n="count", mean="mean", median="median", min="min", max="max", std="std")
            .round(3)
            .sort_values("mean")
        )
        out["by_cohort"] = by_cohort

        # Price index vs the cheapest cohort.
        if len(by_cohort) > 1:
            baseline = by_cohort["mean"].min()
            idx = (by_cohort["mean"] / baseline * 100).round(1)
            out["cohort_price_index"] = idx.to_frame("index_vs_cheapest=100")

    # Price by ZIP.
    out["by_zip"] = (
        df.groupby(["zip", "city", "county", "region", "cohort_label"], dropna=False)["price"]
        .agg(n="count", mean_price="mean", median_price="median")
        .round(3)
        .sort_values("mean_price", ascending=False)
    )

    # Same-product comparison across cohorts (fairest apples-to-apples view).
    if "product_name" in df:
        prod = (
            df.groupby(["product_name", "cohort_label"], dropna=False)["price"]
            .mean()
            .round(3)
            .unstack("cohort_label")
        )
        out["product_by_cohort"] = prod

    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("inputs", nargs="+", help="CSV path(s) or globs.")
    parser.add_argument("--out", default=None, help="Optional CSV to write the cohort summary.")
    args = parser.parse_args()

    df = load_frames(args.inputs)
    print(f"Loaded {len(df)} priced rows across {df['zip'].nunique()} ZIP codes.\n")

    tables = summarize(df)
    for name, table in tables.items():
        print(f"=== {name} ===")
        print(table.to_string())
        print()

    if args.out and "by_cohort" in tables:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        tables["by_cohort"].to_csv(args.out)
        print(f"Wrote cohort summary -> {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
