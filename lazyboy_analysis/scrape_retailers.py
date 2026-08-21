"""Crawl Shopify catalogs of multi-brand furniture retailers.

Both Slumberland and Steinhafels run Shopify, which exposes /products.json:
structured product records carrying vendor (brand), price, SKU and category.
Scraping the retailers rather than the brand sites is deliberate -- most of the
competitor set (Southern Motion, Best, Catnapper, Palliser) is wholesale-only
and publishes no retail price at all. A multi-brand retailer prices La-Z-Boy
and its competitors on the same shelf, which is the comparison we actually want.
"""

import json
import time
import argparse
import urllib.request
from pathlib import Path

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

RETAILERS = {
    "slumberland": "https://www.slumberland.com",
    "steinhafels": "https://www.steinhafels.com",
}

PAGE_SIZE = 250
DELAY = 1.5


def fetch(url, retries=4):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    return None


def crawl(name, base, out_dir):
    products, page = [], 1
    while True:
        data = fetch(f"{base}/products.json?limit={PAGE_SIZE}&page={page}")
        batch = data.get("products", []) if data else []
        if not batch:
            break
        products.extend(batch)
        print(f"  [{name}] page {page:>3}  +{len(batch):>3}  total {len(products)}", flush=True)
        page += 1
        time.sleep(DELAY)

    out = Path(out_dir) / f"{name}_products.json"
    out.write_text(json.dumps(products))
    print(f"  [{name}] wrote {len(products)} products -> {out}", flush=True)
    return products


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    args = ap.parse_args()
    Path(args.out).mkdir(parents=True, exist_ok=True)
    for name, base in RETAILERS.items():
        print(f"== {name} ==", flush=True)
        crawl(name, base, args.out)
