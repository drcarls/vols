"""Was/now prices per cover for La-Z-Boy.com recliners.

The catalogue scrape captured `data-cover-price`, which is the selling price --
the base price on a model with no promotion running, the promotional price on
one that has. The original price lives only in the price block for the cover
currently selected, so recovering it means one request per cover rather than
per model.

That granularity turns out to matter. On the Pinnacle rocking recliner every
cover now sells at $599 while the originals differ ($1,549 and $1,229), so the
promotion flattens a cover ladder that exists at base price. A model that looks
single-priced today is not necessarily single-priced.
"""

import re
import csv
import time
import gzip
import argparse
import urllib.request
from pathlib import Path
from collections import defaultdict

from assortment import own_store_category

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept": "text/html,*/*;q=0.8",
           "Accept-Language": "en-US,en;q=0.9", "Accept-Encoding": "gzip",
           "Sec-Fetch-Mode": "navigate", "Upgrade-Insecure-Requests": "1"}

# The accessible price summary, which states both figures unambiguously.
SALE_RE = re.compile(r"Sale price ([0-9.]+)\. Original price \$([0-9,]+)")
COVER_PRICE_RE = re.compile(r'data-cover-price="([0-9.]+)"')


def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=45) as resp:
                raw = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                return raw.decode("utf-8", errors="ignore")
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(2 ** attempt)
    return None


def covers_to_fetch(path, category):
    out = defaultdict(list)
    for r in csv.DictReader(open(path)):
        if own_store_category(r["product"]) != category:
            continue
        out[(r["product"], r["product_url"])].append(
            (r["cover_id"], r["cover_name"], r["cover_pattern"], float(r["price"])))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--covers", default="data/lazboy_covers.csv")
    ap.add_argument("--category", default="Recliners")
    ap.add_argument("--out", default="data/lazboy_wasnow_recliners.csv")
    ap.add_argument("--delay", type=float, default=1.2)
    a = ap.parse_args()

    todo = covers_to_fetch(a.covers, a.category)
    total = sum(len(v) for v in todo.values())
    print(f"{len(todo)} {a.category.lower()} models, {total} covers", flush=True)

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        done = {(r["product"], r["cover_id"]) for r in csv.DictReader(open(out))}
        print(f"resuming: {len(done)} covers already fetched", flush=True)

    fields = ["product", "product_url", "cover_id", "cover_name", "cover_pattern",
              "now_price", "was_price", "on_promo", "discount_pct"]
    exists = out.exists() and done
    # Written per row so an interrupted run resumes rather than restarting.
    with open(out, "a" if exists else "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        if not exists:
            w.writeheader()
        i = 0
        for (product, url), covers in todo.items():
            for cid, cname, cpat, now in covers:
                i += 1
                if (product, cid) in done:
                    continue
                html = fetch(f"https://www.la-z-boy.com{url}?coverId={cid}")
                was, promo, disc = "", "N", ""
                cur = now
                if html:
                    m = SALE_RE.search(html)
                    if m:
                        cur = float(m.group(1))
                        was = float(m.group(2).replace(",", ""))
                        promo, disc = "Y", round((1 - cur / was) * 100, 1)
                    else:
                        p = COVER_PRICE_RE.findall(html)
                        cur = float(p[0]) if p else now
                w.writerow({"product": product, "product_url": url, "cover_id": cid,
                            "cover_name": cname, "cover_pattern": cpat,
                            "now_price": cur, "was_price": was,
                            "on_promo": promo, "discount_pct": disc})
                fh.flush()
                if i % 50 == 0:
                    print(f"   {i}/{total}", flush=True)
                time.sleep(a.delay)
    print(f"\ndone -> {out}")
