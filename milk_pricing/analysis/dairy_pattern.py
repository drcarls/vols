"""Is fluid milk priced differently from other dairy? Aldi, 20 SC stores.

data/aldi_sc_observations.json holds 500 product observations: 25 products at
each of 20 South Carolina ZIPs, pulled in one pass. That makes it a ready-made
within-store cross-product panel — the same design the Walmart comparison
basket is meant to provide, on a different retailer.

Two guards matter:
  * Two products mix 0.5 gal and 1 gal rows, so raw price conflates size.
    Everything is normalized ($/gal for fluid, $/oz for solids) before comparison.
  * The file's own `category` field is unreliable (it labels vegetable oil
    sticks "dairy_white"), so tiers are assigned explicitly below.

Backs reports/dairy_pattern.md.
"""
import csv
import json
from collections import defaultdict

import numpy as np

FLUID = {"Friendly Farms Whole Milk", "Friendly Farms 2% Milk",
         "Friendly Farms Low Fat Chocolate Milk"}
BUTTER_EGGS = {"Countryside Creamery Salted Butter Sticks",
               "Countryside Creamery Unsalted Butter Sticks",
               "Countryside Creamery Pure Irish Butter Salted",
               "Goldhen Grade A Large White Eggs, 1 dozen"}
TIERS = ("FLUID MILK", "butter & eggs", "other dairy & grocery")


def tier(name):
    return TIERS[0] if name in FLUID else TIERS[1] if name in BUTTER_EGGS else TIERS[2]


def normalized():
    """{zip: {product: unit price}} — $/gal for fluid milk, $/oz for solids."""
    out = defaultdict(dict)
    for x in json.load(open("data/aldi_sc_observations.json")):
        if x["name"] in FLUID and x.get("price_per_gal"):
            v = x["price_per_gal"]
        elif x.get("fl_oz"):
            v = x["price"] / x["fl_oz"]
        else:
            v = x["price"]
        out[x["zip_code"]].setdefault(x["name"], v)
    return out


def main():
    byz = normalized()
    prod = defaultdict(list)
    for r in byz.values():
        for p, v in r.items():
            prod[p].append(v)
    rows = [(p, v, 100 * np.std(v) / np.mean(v), len({round(x, 4) for x in v}))
            for p, v in prod.items() if len(v) >= 10]
    print(f"=== Aldi, {len(byz)} SC stores, size-normalized ===")
    for t in TIERS:
        g = [r for r in rows if tier(r[0]) == t]
        print(f"\n  {t}  ({len(g)} products)")
        for p, v, cv, dis in sorted(g, key=lambda r: -r[2]):
            print(f"    {p[:50]:<52} n={len(v):>2}  CV {cv:>5.1f}%   {dis:>2} distinct price(s)")
        print(f"    -> mean CV {np.mean([r[2] for r in g]):.1f}%   "
              f"one price across all of SC: {sum(1 for r in g if r[3] == 1)}/{len(g)}")

    print("\n=== Aldi vs Walmart whole milk, same ZIPs ===")
    W = {r["zip"].zfill(5): float(r["whole_milk"])
         for r in csv.DictReader(open("data/sc_walmart_official.csv")) if r["whole_milk"]}
    pairs = [(z, byz[z]["Friendly Farms Whole Milk"], W[z]) for z in byz
             if "Friendly Farms Whole Milk" in byz[z] and z in W]
    if len(pairs) >= 6:
        a = np.array([p[1] for p in pairs])
        w = np.array([p[2] for p in pairs])
        print(f"  {len(pairs)} ZIPs with both   correlation r = {np.corrcoef(a, w)[0, 1]:+.3f}")
        under = sum(1 for _, av, wv in pairs if wv < av)
        print(f"  Walmart below Aldi in {under}/{len(pairs)} markets; "
              f"median spread ${np.median(w - a):+.2f}")
        for z, av, wv in sorted(pairs, key=lambda p: p[1]):
            print(f"    {z}  Aldi ${av:>5.2f}  Walmart ${wv:>5.2f}  spread ${wv - av:>+5.2f}")

    print("\n=== Does Aldi's milk price track ZIP demographics? (n is small) ===")
    meta = {}
    for r in csv.DictReader(open("data/national_walmart_official.csv")):
        if r["zip"] and r["pct_black"] and r["median_income"]:
            meta[r["zip"].zfill(5)] = (float(r["pct_black"]), float(r["median_income"]))
    Z = [z for z in byz if z in meta and "Friendly Farms Whole Milk" in byz[z]]
    if len(Z) >= 10:
        y = np.array([byz[z]["Friendly Farms Whole Milk"] for z in Z])
        X = np.column_stack([np.ones(len(Z)), [meta[z][0] for z in Z],
                             np.array([meta[z][1] for z in Z]) / 1000])
        b, *_ = np.linalg.lstsq(X, y, rcond=None)
        res = y - X @ b
        se = np.sqrt(np.diag(np.linalg.pinv(X.T @ X)) * (res @ res / (len(Z) - 3)))
        print(f"  n={len(Z)} ZIPs   %Black {b[1]:+.5f} (t {b[1]/se[1]:+.2f})   "
              f"income {b[2]:+.5f} (t {b[2]/se[2]:+.2f})")
        print("  -> 20 ZIPs is too thin for inference; reported for completeness only.")


if __name__ == "__main__":
    main()
