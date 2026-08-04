#!/usr/bin/env python3
"""CLI entry point: scrape Instacart milk prices across ZIP codes via Bright Data.

Usage examples
--------------
  # Recommended: Bright Data managed Instacart Web Scraper API
  python scrape.py --strategy dataset

  # DIY fallback via Web Unlocker
  python scrape.py --strategy unlocker

  # Limit the run while testing
  python scrape.py --strategy dataset --max-zips 3 --max-products 2

Config files
------------
  config/zips.csv      one row per ZIP (zip,city,county,region,cohort_label)
  config/products.csv  one row per search term (query,category,notes)

Output
------
  data/milk_prices_<timestamp>.csv   normalized price rows
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

# Make src/ importable whether run from repo root or from milk_price_scraper/.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "src"))

try:
    from dotenv import load_dotenv

    load_dotenv(HERE / ".env")
except ImportError:
    pass  # dotenv is optional; env vars can be exported directly.

from brightdata_client import BrightDataClient, BrightDataError  # noqa: E402
import instacart_scraper as ic  # noqa: E402


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return [row for row in csv.DictReader(fh)]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_dataset(
    client: BrightDataClient,
    zips: list[dict[str, str]],
    products: list[dict[str, str]],
    retailers: list[str] | None,
    poll_interval: int,
    max_wait: int,
) -> list[dict]:
    scraped_at = utc_now()
    inputs = ic.build_dataset_inputs(zips, products, retailers)
    print(f"[dataset] Triggering collection: {len(inputs)} input rows "
          f"({len(zips)} zips x {len(products)} products)...")
    raw_rows = client.collect_dataset(
        inputs, poll_interval=poll_interval, max_wait=max_wait
    )
    print(f"[dataset] Received {len(raw_rows)} raw rows from Bright Data.")

    zip_by_code = {z["zip"]: z for z in zips}
    records: list[dict] = []
    for raw in raw_rows:
        code = str(raw.get("zipcode") or raw.get("zip") or "")
        zip_meta = zip_by_code.get(code, {"zip": code})
        query = str(raw.get("keyword") or raw.get("query") or "")
        rec = ic.normalize_dataset_row(raw, zip_meta, query, scraped_at)
        records.append(rec.as_row())
    return records


def run_unlocker(
    client: BrightDataClient,
    zips: list[dict[str, str]],
    products: list[dict[str, str]],
) -> list[dict]:
    records: list[dict] = []
    for z in zips:
        for p in products:
            scraped_at = utc_now()
            query = p["query"]
            url = f"https://www.instacart.com/store/s?k={quote_plus(query)}"
            print(f"[unlocker] {z['zip']} :: {query}")
            try:
                html = client.unlock(url)
            except BrightDataError as exc:
                print(f"  ! unlock failed: {exc}", file=sys.stderr)
                continue
            raw_products = ic.parse_unlocker_html(html)
            if not raw_products:
                print("  (no products parsed -- Instacart is geo-gated; "
                      "the dataset strategy is more reliable)")
            for raw in raw_products:
                rec = ic.normalize_unlocker_row(raw, z, query, scraped_at)
                records.append(rec.as_row())
    return records


def write_output(records: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=ic.FIELDNAMES)
        writer.writeheader()
        for rec in records:
            writer.writerow(rec)
    print(f"\nWrote {len(records)} rows -> {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strategy", choices=["dataset", "unlocker"], default="dataset")
    parser.add_argument("--zips", default=str(HERE / "config" / "zips.csv"))
    parser.add_argument("--products", default=str(HERE / "config" / "products.csv"))
    parser.add_argument("--out", default=None, help="Output CSV path.")
    parser.add_argument("--retailers", default=None,
                        help="Comma-separated retailer filter (dataset strategy only).")
    parser.add_argument("--max-zips", type=int, default=None)
    parser.add_argument("--max-products", type=int, default=None)
    parser.add_argument("--poll-interval", type=int, default=10)
    parser.add_argument("--max-wait", type=int, default=1800)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the input JSON that would be sent to Bright Data "
                             "(dataset strategy) or the URLs (unlocker) and exit. "
                             "Makes no API calls and spends no credits.")
    args = parser.parse_args()

    zips = load_csv(Path(args.zips))
    products = load_csv(Path(args.products))
    if args.max_zips:
        zips = zips[: args.max_zips]
    if args.max_products:
        products = products[: args.max_products]
    retailers = [r.strip() for r in args.retailers.split(",")] if args.retailers else None

    if not zips or not products:
        print("No zips or products loaded -- check config CSVs.", file=sys.stderr)
        return 2

    if args.dry_run:
        import json
        if args.strategy == "dataset":
            inputs = ic.build_dataset_inputs(zips, products, retailers)
            print(f"[dry-run] {len(inputs)} dataset input rows "
                  f"({len(zips)} zips x {len(products)} products). "
                  f"Verify these field names match your dataset's input schema:\n")
            print(json.dumps(inputs[:5], indent=2))
            if len(inputs) > 5:
                print(f"... and {len(inputs) - 5} more.")
        else:
            for z in zips:
                for p in products:
                    q = quote_plus(p["query"])
                    print(f"{z['zip']}  https://www.instacart.com/store/s?k={q}")
        return 0

    try:
        client = BrightDataClient()
    except BrightDataError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    if args.strategy == "dataset":
        records = run_dataset(client, zips, products, retailers,
                              args.poll_interval, args.max_wait)
    else:
        records = run_unlocker(client, zips, products)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = Path(args.out) if args.out else HERE / "data" / f"milk_prices_{stamp}.csv"
    write_output(records, out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
