"""Franklin against La-Z-Boy on Slumberland's recliner wall.

Franklin is Slumberland's second-largest recliner brand and was on nobody's
competitor list. Everything here works at model level, taking each model's
cheapest configuration -- the price a shopper is quoted to get into that model
-- because SKU counts reward brands that stock more colourways rather than more
range.
"""

import re
import argparse
import statistics as st
from collections import defaultdict

from assortment import load, load_descriptions, FEATURES

BANDS = [(0, 600), (600, 800), (800, 1000), (1000, 1300), (1300, 1700), (10**9, 10**9)]


def med(v):
    return st.median(v) if v else None


def entry_models(rows, brand):
    """One row per model: its cheapest configuration."""
    by = defaultdict(list)
    for r in rows:
        if r["brand"] == brand:
            by[r["product_id"]].append(r)
    return [min(v, key=lambda x: x["price"]) for v in by.values()]


def band_label(lo, hi):
    return f"${lo:,}-{hi:,}" if hi < 10**9 else f"${lo:,}+"


def main(a):
    rows = [r for r in load(a.skus, load_descriptions())
            if r["retailer"] == a.retailer and r["cat"] == a.category]
    lz, fr = entry_models(rows, a.focus), entry_models(rows, a.rival)

    print(f"{a.focus} {len(lz)} models   ·   {a.rival} {len(fr)} models"
          f"   ({a.retailer}, {a.category.lower()})\n")

    # The comparison that matters: list position and markdown depth, band by
    # band. A single median hides that the two brands reach the same shelf
    # price from opposite directions.
    print("LIST POSITION AND MARKDOWN, BY SELLING-PRICE BAND\n")
    print(f"{'band':<15}{a.focus + ' n':>9}{'list':>9}{'disc':>7}"
          f"{'   ':<3}{a.rival + ' n':>9}{'list':>9}{'disc':>7}{'lists above?':>15}")
    print("-" * 86)
    for lo, hi in BANDS[:-1]:
        A = [x for x in lz if lo <= x["price"] < (hi if hi < 10**9 else 10**12)]
        B = [x for x in fr if lo <= x["price"] < (hi if hi < 10**9 else 10**12)]
        if not A and not B:
            continue
        f = lambda v, k: med([float(x[k]) for x in v if x[k]]) or 0
        la, lb = f(A, "list_price"), f(B, "list_price")
        flag = a.rival if lb > la else (a.focus if la > lb else "level")
        print(f"{band_label(lo, hi):<15}{len(A):>9}{la:>9,.0f}{f(A,'discount_pct'):>6.0f}%"
              f"{'   ':<3}{len(B):>9}{lb:>9,.0f}{f(B,'discount_pct'):>6.0f}%{flag:>15}")

    # How completely one brand shadows the other's price points.
    shadowed = {x["product"] for x in fr
                if any(abs(x["price"] - y["price"]) / y["price"] <= a.window for y in lz)}
    print(f"\n{len(shadowed)} of {len(fr)} {a.rival} models sit within "
          f"{a.window*100:.0f}% of a {a.focus} model")

    top = [x for x in lz if x["price"] >= a.premium]
    rival_top = [x for x in fr if x["price"] >= a.premium]
    print(f"At ${a.premium:,}+: {a.focus} {len(top)} models, {a.rival} {len(rival_top)}")

    print("\nFEATURES ADVERTISED, share of models\n")
    print(f"{'feature':<16}{a.focus:>12}{a.rival:>12}")
    print("-" * 40)
    for k, pat in FEATURES.items():
        x = sum(1 for m in lz if re.search(pat, m["product"], re.I)) / len(lz) * 100
        y = sum(1 for m in fr if re.search(pat, m["product"], re.I)) / len(fr) * 100
        if max(x, y) >= 8:
            print(f"{k:<16}{x:>11.0f}%{y:>11.0f}%")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--skus", default="data/skus.csv")
    ap.add_argument("--retailer", default="slumberland")
    ap.add_argument("--category", default="Recliners")
    ap.add_argument("--focus", default="La-Z-Boy")
    ap.add_argument("--rival", default="Franklin")
    ap.add_argument("--window", type=float, default=0.10)
    ap.add_argument("--premium", type=int, default=1600)
    main(ap.parse_args())
