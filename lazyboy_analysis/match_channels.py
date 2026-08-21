"""Match La-Z-Boy models across its three retail channels.

La-Z-Boy sells the same frames through its own stores and through independent
dealers. Comparing a model's price across those channels is the one check the
manufacturer usually cannot run on itself, because almost nobody sees both
sides of the wholesale/retail line at once.

Matching is on model family + form + motion rather than on SKU: the three
channels use different SKU schemes, but they all keep La-Z-Boy's model names
("Pinnacle", "Trouper", "James"), which is the only join key common to all of
them. A match is therefore same-model-same-configuration, not same-SKU.
"""

import csv
import re
import argparse
import statistics as st
from collections import defaultdict

# Words describing configuration or trim rather than the model itself.
CONFIG_RE = re.compile(
    r"\b(power|plus|duo|rocking|rocker|reclining|recliner|high leg|sofa|"
    r"loveseat|sectional|chair|w/|with|headrest|lumbar|console|lift|massage|"
    r"heat|bronze|gold|platinum|petite|manual|swivel|glider|full|reclina|"
    r"wall|stationary|apartment|queen|sleeper|ottoman)\b", re.I)

FORMS = [
    ("Sectional", r"sectional"),
    ("Loveseat", r"loveseat"),
    ("Sofa", r"\bsofa\b"),
    ("Recliner", r"recliner|reclining chair|lift chair"),
    ("Chair", r"\bchair\b"),
]

POWER_RE = re.compile(r"\bpower\b|\bduo\b|\blift\b", re.I)


def model_family(title):
    t = re.sub(r"[®™]", "", title or "")
    t = CONFIG_RE.sub(" ", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def form_of(title):
    for name, pattern in FORMS:
        if re.search(pattern, title or "", re.I):
            return name
    return "Other"


def config_key(title):
    """Model + form + drive type -- the granularity a buyer would call 'the same chair'."""
    return (model_family(title), form_of(title),
            "Power" if POWER_RE.search(title or "") else "Manual")


def load_dealers(path):
    out = defaultdict(list)
    for r in csv.DictReader(open(path)):
        if r["brand"] != "La-Z-Boy":
            continue
        out[config_key(r["title"])].append({
            "retailer": r["retailer"],
            "title": r["title"],
            "price": float(r["price"]),
            "list": float(r["list_price"]) if r["list_price"] else None,
        })
    return out


def load_own(path):
    """La-Z-Boy.com quotes a price per cover; the base cover is the comparable figure."""
    by_product = defaultdict(list)
    for r in csv.DictReader(open(path)):
        by_product[r["product"]].append(float(r["price"]))
    out = defaultdict(list)
    for product, prices in by_product.items():
        out[config_key(product)].append({
            "retailer": "la-z-boy.com",
            "title": product,
            "price": min(prices),
            "max_cover": max(prices),
            "covers": len(prices),
        })
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default="data/catalog.csv")
    ap.add_argument("--covers", default="data/lazboy_covers.csv")
    ap.add_argument("--out", default="data/channel_matches.csv")
    args = ap.parse_args()

    dealers, own = load_dealers(args.catalog), load_own(args.covers)
    keys = sorted(set(dealers) & set(own))

    rows = []
    for k in keys:
        model, form, drive = k
        o = own[k][0]
        for d in dealers[k]:
            rows.append({
                "model": model, "form": form, "drive": drive,
                "lzb_title": o["title"], "lzb_base": o["price"],
                "lzb_top_cover": o["max_cover"],
                "dealer": d["retailer"], "dealer_title": d["title"],
                "dealer_price": d["price"], "dealer_list": d["list"] or "",
                "vs_lzb_base_pct": round((d["price"] / o["price"] - 1) * 100, 1),
            })

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"matched configurations: {len(keys)}   dealer rows: {len(rows)}")
    print(f"wrote -> {args.out}\n")

    print(f"{'model':<16}{'form':<11}{'drive':<8}{'lzb.com':>9}{'dealer':>12}{'price':>9}{'vs .com':>9}")
    print("-" * 76)
    for r in sorted(rows, key=lambda r: -abs(r["vs_lzb_base_pct"]))[:22]:
        print(f"{r['model'][:15]:<16}{r['form']:<11}{r['drive']:<8}"
              f"{r['lzb_base']:>9,.0f}{r['dealer'][:11]:>12}"
              f"{r['dealer_price']:>9,.0f}{r['vs_lzb_base_pct']:>8.0f}%")

    gaps = [r["vs_lzb_base_pct"] for r in rows]
    print(f"\nmedian dealer price vs la-z-boy.com base: {st.median(gaps):+.0f}%")
    for ret in ("slumberland", "steinhafels"):
        g = [r["vs_lzb_base_pct"] for r in rows if r["dealer"] == ret]
        if g:
            print(f"  {ret:<14} n={len(g):<4} median {st.median(g):+.0f}%   "
                  f"range {min(g):+.0f}% to {max(g):+.0f}%")
