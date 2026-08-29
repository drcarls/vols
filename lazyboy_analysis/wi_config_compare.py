"""Steinhafels vs La-Z-Boy's own Wisconsin stores, matched on configuration.

The earlier collection-level match compared a dealer's fully loaded chair to
la-z-boy.com's base cover and reported a 65% dealer premium that was really a
spec difference. This pairs on configuration -- collection, form, drive, and the
headrest / lumbar / wall / high-leg / lift attributes -- and prices each
La-Z-Boy.com side at the two Wisconsin zones (Wauwatosa in the modal zone,
Madison alone in its own, higher one).

Where Steinhafels' cover id also appears on the La-Z-Boy.com page the comparison
is cover-for-cover; otherwise it is against La-Z-Boy.com's cheapest fabric cover,
which is a floor, so the dealer gap it reports is an upper bound.
"""

import re
import csv
import json
import time
import gzip
import urllib.request
from pathlib import Path
from statistics import median

from match_config import key, is_leather

STORES = {"Wauwatosa": "50860739", "Madison": "50855884"}
BASE = "https://www.la-z-boy.com"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

COVER_RE = re.compile(
    r'data-cover-id="([A-Za-z0-9]+)"[^>]*data-cover-price="([0-9.]+)"')
COVER_ANY = re.compile(
    r'data-cover-price="([0-9.]+)"[^>]*?data-cover-id="([A-Za-z0-9]+)"')
SALE_RE = re.compile(r"Sale price ([0-9.]+)\. Original price \$([0-9,]+)")


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


def covers(html):
    """cover id -> selling price, from whichever attribute order the page uses."""
    out = {}
    for cid, price in COVER_RE.findall(html):
        out[cid] = float(price)
    for price, cid in COVER_ANY.findall(html):
        out.setdefault(cid, float(price))
    return out


def leather(cid):
    return cid.upper().startswith("LB")


def build_pairs():
    """Steinhafels La-Z-Boy items paired to the same configuration on lzb.com."""
    lzb = {}
    for r in csv.DictReader(open("data/lazboy_covers.csv")):
        lzb.setdefault(r["product"], r["product_url"])
    lzb_key = {}
    for product, url in lzb.items():
        lzb_key.setdefault(key(product), (product, url))

    rows = [r for r in csv.DictReader(open("data/skus.csv"))
            if r["retailer"] == "steinhafels" and r["brand"] == "La-Z-Boy"]

    pairs, skipped = {}, {"no match": set(), "leather only": set()}
    for r in rows:
        k = key(r["product"])
        hit = lzb_key.get(k)
        if not hit:
            skipped["no match"].add(r["product"])
            continue
        if is_leather(r["product"]) or r["material"] == "Leather":
            skipped["leather only"].add(r["product"])
            continue
        cover = (r["variant"] or "").split()[0] if r["variant"] else ""
        # Keep the cheapest Steinhafels cover of each configuration, so both
        # sides are entry covers of the same frame.
        cur = pairs.get(k)
        price = float(r["price"] or 0)
        if not price:
            continue
        if cur is None or price < cur["stein_price"]:
            pairs[k] = {"key": k, "stein_product": r["product"],
                        "stein_price": price,
                        "stein_list": float(r["list_price"] or 0) or None,
                        "stein_cover": cover,
                        "lzb_product": hit[0], "lzb_url": hit[1]}
    return list(pairs.values()), skipped


if __name__ == "__main__":
    pairs, skipped = build_pairs()
    print(f"{len(pairs)} configuration matches; "
          f"{len(skipped['no match'])} unmatched, "
          f"{len(skipped['leather only'])} leather-only skipped", flush=True)

    for p in pairs:
        for city, sid in STORES.items():
            html = fetch(BASE + p["lzb_url"], sid)
            if not html:
                p[city] = None
                continue
            cs = covers(html)
            fabric = {c: v for c, v in cs.items() if not leather(c)}
            same = cs.get(p["stein_cover"])
            p[city] = same if same else (min(fabric.values()) if fabric else None)
            p[city + "_basis"] = "same cover" if same else "cheapest fabric"
            p[city + "_ncovers"] = len(cs)
            m = SALE_RE.search(html)
            p[city + "_promo"] = "Y" if m else "N"
            time.sleep(0.8)
        print(f"  {p['stein_product'][:44]:44s} "
              f"stein {p['stein_price']:>8.0f}  "
              f"waut {p.get('Wauwatosa') or 0:>8.0f}  "
              f"mad {p.get('Madison') or 0:>8.0f}  "
              f"({p.get('Wauwatosa_basis','-')})", flush=True)

    fields = ["stein_product", "lzb_product", "stein_cover", "stein_price",
              "stein_list", "Wauwatosa", "Wauwatosa_basis", "Wauwatosa_promo",
              "Madison", "Madison_basis", "Madison_promo"]
    out = Path("data/wi_config_compare.csv")
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for p in pairs:
            w.writerow(p)
    json.dump({"unmatched": sorted(skipped["no match"]),
               "leather_only": sorted(skipped["leather only"])},
              open("data/wi_config_skipped.json", "w"), indent=1)

    for city in STORES:
        gaps = [(p["stein_price"] / p[city] - 1) * 100
                for p in pairs if p.get(city)]
        same = [p for p in pairs if p.get(city + "_basis") == "same cover"]
        if gaps:
            print(f"\n{city}: n={len(gaps)}  median gap {median(gaps):+.0f}%  "
                  f"({len(same)} cover-for-cover)")
