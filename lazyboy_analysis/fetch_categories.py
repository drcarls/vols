"""Fetch Steinhafels category collections.

Steinhafels' product_type is a warehouse status ("Regular Inventory"), not a
category, so category has to come from collection membership instead.
"""

import json
import time
import argparse
import urllib.request
from pathlib import Path

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Upholstered seating only -- the segment where La-Z-Boy competes.
CATEGORIES = [
    "recliners",
    "reclining-sofas-loveseats",
    "reclining-sectionals",
    "sofas",
    "loveseats",
    "sectionals",
    "accent-chairs",
]

BASE = "https://www.steinhafels.com"


def fetch(url, retries=4):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    return None


def fetch_collection(handle):
    ids, page = {}, 1
    while True:
        data = fetch(f"{BASE}/collections/{handle}/products.json?limit=250&page={page}")
        batch = data.get("products", []) if data else []
        if not batch:
            break
        for p in batch:
            ids[p["id"]] = handle
        page += 1
        time.sleep(1.2)
    return ids


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    args = ap.parse_args()
    Path(args.out).mkdir(parents=True, exist_ok=True)

    mapping = {}
    for handle in CATEGORIES:
        got = fetch_collection(handle)
        # First category wins: the list runs specific -> general, so a reclining
        # sofa lands in "reclining-sofas-loveseats" rather than plain "sofas".
        for pid, cat in got.items():
            mapping.setdefault(str(pid), cat)
        print(f"  {handle:>26}: {len(got):>4} products", flush=True)

    out = Path(args.out) / "steinhafels_categories.json"
    out.write_text(json.dumps(mapping))
    print(f"  mapped {len(mapping)} products -> {out}")
