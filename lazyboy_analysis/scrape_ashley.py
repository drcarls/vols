"""Scrape Ashley's own catalogue.

Ashley returns 403 to a desktop user-agent but serves a mobile one, which is
what makes this reachable at all. Browse runs on Constructor.io, whose public
API returns the catalogue with dimensions and a description but deliberately
without price -- Ashley prices vary by store. Price therefore comes from each
product page's schema.org block, one fetch per product.

Output matches the recliner export already in data/, so both feed the same
analysis.
"""

import re
import csv
import json
import time
import gzip
import argparse
import urllib.request
from pathlib import Path

# The desktop UA is refused; this one is not.
UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
CONSTRUCTOR_KEY = "key_K0xLx6sleKg7RBXp"
BROWSE = "https://ac.cnstrc.com/browse/group_id/{group}"

# "Motion sofas" here means sofas and loveseats with a reclining action, the
# same definition used for the dealer feeds. Sectionals are a separate form.
GROUPS = {
    "reclining-sofas-couches": "Motion sofas",
    "reclining-loveseats": "Motion sofas",
}

LD_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
LEATHER_RE = re.compile(r"\bleather\b", re.I)
PERFORMANCE_RE = re.compile(r"performance fabric|nuvella|durapella", re.I)
FABRIC_RE = re.compile(r"polyester|chenille|linen|velvet|fabric|upholstery", re.I)

MECHANISM = [
    ("lift", r"\blift\b"),
    ("rocker", r"\brocker|rocking\b"),
    ("glider", r"\bglider|gliding|swivel\b"),
    ("standard", r""),
]


def fetch(url, as_json=False, retries=4):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "application/json" if as_json else "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=45) as resp:
                raw = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                text = raw.decode("utf-8", errors="ignore")
                return json.loads(text) if as_json else text
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(2 ** attempt)
    return None


def browse(group, page_size=100):
    """Every product in a browse group, paginated."""
    out, page = [], 1
    while True:
        url = (f"{BROWSE.format(group=group)}?key={CONSTRUCTOR_KEY}"
               f"&num_results_per_page={page_size}&page={page}"
               f"&c=ciojs-client-2.62.0&i=catalog-audit&s=1")
        data = fetch(url, as_json=True)
        if not data:
            break
        resp = data.get("response", {})
        results = resp.get("results", [])
        if not results:
            break
        out.extend(results)
        if len(out) >= resp.get("total_num_results", 0):
            break
        page += 1
        time.sleep(1)
    return out


def material_of(description):
    """Ashley states upholstery in the product description."""
    if LEATHER_RE.search(description or ""):
        return "leather"
    if PERFORMANCE_RE.search(description or ""):
        return "performance"
    if FABRIC_RE.search(description or ""):
        return "fabric"
    return "unknown"


def mechanism_of(name):
    for label, pattern in MECHANISM:
        if not pattern or re.search(pattern, name or "", re.I):
            return label
    return "standard"


def price_of(url):
    """Selling price from the product page's schema.org block."""
    html = fetch(url)
    if not html:
        return None
    for blob in LD_RE.findall(html):
        try:
            data = json.loads(blob)
        except json.JSONDecodeError:
            continue
        if data.get("@type") != "Product":
            continue
        offers = data.get("offers") or {}
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        try:
            return float(offers.get("price"))
        except (TypeError, ValueError):
            return None
    return None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/ashley_own_motion_sofas.csv")
    ap.add_argument("--delay", type=float, default=1.0)
    args = ap.parse_args()

    seen, rows = set(), []
    for group, category in GROUPS.items():
        results = browse(group)
        print(f"  {group:<28} {len(results)} products", flush=True)
        for r in results:
            d = r.get("data", {})
            pid = str(d.get("id") or "")
            if not pid or pid in seen:
                continue
            seen.add(pid)
            rows.append({
                "product_id": pid,
                "name": r.get("value", ""),
                "mechanism": mechanism_of(r.get("value", "")),
                "subcategory": category,
                "material": material_of(d.get("description", "")),
                "price": None,
                "width_in": d.get("productWidthIn", ""),
                "depth_in": d.get("productDepthIn", ""),
                "height_in": d.get("productHeightIn", ""),
                "brand": d.get("facetBrand", ""),
                "color": d.get("color", ""),
                "url": d.get("url", ""),
            })
        time.sleep(args.delay)

    # One page fetch per product, so the file is written as it goes and an
    # interrupted run resumes instead of starting over.
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {}
    if out.exists():
        done = {r["product_id"]: r for r in csv.DictReader(open(out))}
        print(f"  resuming: {len(done)} already priced", flush=True)

    fields = list(rows[0].keys())
    todo = [r for r in rows if r["product_id"] not in done]
    print(f"\n  fetching prices for {len(todo)} products", flush=True)

    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in done.values():
            w.writerow({k: r.get(k, "") for k in fields})
        fh.flush()

        got = len(done)
        for i, r in enumerate(todo, 1):
            r["price"] = price_of(r["url"])
            if r["price"]:
                w.writerow(r)
                fh.flush()
                got += 1
            if i % 25 == 0:
                print(f"   {i}/{len(todo)}  priced {got}", flush=True)
            time.sleep(args.delay)

    print(f"\nwrote {got} priced products -> {out}")
