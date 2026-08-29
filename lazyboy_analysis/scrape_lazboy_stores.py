"""Probe La-Z-Boy.com prices across every store to find the pricing zones.

La-Z-Boy.com prices are store-scoped. Visiting a store page does not change
them -- the site pins `preferredStoreSet` server-side, apparently by geo-IP --
but setting that cookie directly does, and the same cover comes back at
different prices with different was figures.

Full coverage would be 376 stores by 226 models, which is not worth running:
stores appear to share zone prices (two Albuquerque stores agree, and Alexandria
VA matches Algonquin IL). So this probes a small basket across every store,
which is enough to recover the zones. Once the zones are known, a full catalogue
run needs one store per zone rather than all 376.

The basket spans a promoted and an unpromoted recliner plus two motion sofas, so
a zone difference in base price is distinguishable from a difference in what is
on promotion.
"""

import re
import csv
import time
import gzip
import argparse
import urllib.request
from pathlib import Path

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

BASKET = [
    ("Pinnacle Rocking Recliner", "Recliners",
     "/p/living-room/recliners/rocking-recliners/pinnacle-rocking-recliner/R-010512", "B153808"),
    ("Jasper Rocking Recliner", "Recliners",
     "/p/living-room/recliners/rocking-recliners/jasper-rocking-recliner/R-010709", "B153808"),
    ("Brooks Reclining Sofa", "Motion sofas",
     "/p/sofas-sectionals/reclining-sofas-sectionals/reclining-sofas/brooks-reclining-sofa/R-444727", "B153808"),
    ("Trouper Reclining Sofa", "Motion sofas",
     "/p/sofas-sectionals/reclining-sofas-sectionals/reclining-sofas/trouper-reclining-sofa/R-444724", "D212432"),
]

SALE_RE = re.compile(r"Sale price ([0-9.]+)\. Original price \$([0-9,]+)")
COVER_RE = re.compile(r'data-cover-price="([0-9.]+)"')


def fetch(url, store_id, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA, "Accept": "text/html,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9", "Accept-Encoding": "gzip",
                "Sec-Fetch-Mode": "navigate", "Upgrade-Insecure-Requests": "1",
                "Cookie": f"preferredStoreSet={store_id}"})
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


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stores", default="data/lzb_store_ids.txt")
    ap.add_argument("--out", default="data/lazboy_store_prices.csv")
    ap.add_argument("--delay", type=float, default=1.0)
    a = ap.parse_args()

    ids = [x.strip() for x in open(a.stores) if x.strip()]
    out = Path(a.out)
    done = set()
    if out.exists():
        done = {(r["store_id"], r["product"]) for r in csv.DictReader(open(out))}
        print(f"resuming: {len(done)} probes already done", flush=True)

    fields = ["store_id", "product", "category", "cover_id",
              "now_price", "was_price", "on_promo"]
    exists = out.exists() and done
    print(f"{len(ids)} stores x {len(BASKET)} products = {len(ids)*len(BASKET)} probes", flush=True)

    with open(out, "a" if exists else "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        if not exists:
            w.writeheader()
        n = 0
        for sid in ids:
            for name, cat, url, cover in BASKET:
                n += 1
                if (sid, name) in done:
                    continue
                html = fetch(f"https://www.la-z-boy.com{url}?coverId={cover}", sid)
                now = was = ""
                promo = "N"
                if html:
                    m = SALE_RE.search(html)
                    if m:
                        now = float(m.group(1))
                        was = float(m.group(2).replace(",", ""))
                        promo = "Y"
                    else:
                        p = COVER_RE.findall(html)
                        now = float(p[0]) if p else ""
                w.writerow({"store_id": sid, "product": name, "category": cat,
                            "cover_id": cover, "now_price": now,
                            "was_price": was, "on_promo": promo})
                fh.flush()
                time.sleep(a.delay)
            if n % 80 == 0:
                print(f"   {n}/{len(ids)*len(BASKET)}", flush=True)
    print(f"\ndone -> {out}")
