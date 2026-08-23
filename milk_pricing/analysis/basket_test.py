"""Comparison-basket test: is fluid milk uniquely variable among Great Value items?

The claim under test (client recollection, 2014): Walmart's other private-brand
items were not priced like milk. If GV milk disperses across stores and GV flour
does not, that is a category carve-out — and, more importantly, it licenses a
WITHIN-STORE PLACEBO: differencing milk against a non-KVI item at the same store
removes every store-level confound (cost, freight, format, competition,
demographics of the trade area) that has dogged every store-to-store comparison
in this project.

Input: a basket file covering the SAME stores as data/national_walmart_official.csv,
collected by the SAME method. Either shape works:

  long  store_id,zip,item,price          (one row per store x item)
  wide  store_id,zip,<item1>,<item2>,...  (one column per item)

Demographics, county, geo and state are joined from the national milk file by ZIP,
so the basket file needs only store_id/zip, the item, and the price.

Usage:
    python3 analysis/basket_test.py data/walmart_basket.csv
    python3 analysis/basket_test.py --selftest      # synthetic data, verifies the code path
"""
import csv
import math
import statistics
import sys
from collections import defaultdict

import numpy as np

# Items expected to behave like traffic drivers (KVI) vs pantry staples.
KVI = {"whole_milk", "milk_2pct", "eggs_12ct", "white_bread", "bananas"}
PANTRY = {"flour_5lb", "green_beans_can", "veg_oil_48oz", "ketchup_20oz", "paper_towels"}
ID_COLS = {"store_id", "zip", "state", "county", "geo", "item", "price", "size_text"}


def load_meta():
    meta = {}
    for r in csv.DictReader(open("data/national_walmart_official.csv")):
        if not (r["zip"] and r["state"] and r["county"] and r["pct_black"]
                and r["median_income"] and r["population"]):
            continue
        meta[r["zip"].zfill(5)] = {
            "st": r["state"], "cty": r["county"], "geo": r["geo"],
            "blk": float(r["pct_black"]), "inc": float(r["median_income"]),
            "pop": float(r["population"]),
            "milk": float(r["whole_milk"]) if r["whole_milk"] else None,
        }
    return meta


def load_basket(path):
    """Return {zip: {item: price}}, accepting long or wide layout."""
    rows = list(csv.DictReader(open(path)))
    if not rows:
        sys.exit(f"{path} is empty")
    out = defaultdict(dict)
    if "item" in rows[0] and "price" in rows[0]:
        for r in rows:
            if r.get("price") and r.get("zip"):
                out[r["zip"].zfill(5)][r["item"].strip()] = float(r["price"])
    else:
        items = [c for c in rows[0] if c not in ID_COLS and c.strip()]
        for r in rows:
            if not r.get("zip"):
                continue
            for it in items:
                if r.get(it):
                    out[r["zip"].zfill(5)][it] = float(r[it])
    return out


def ols(cols, y):
    X = np.column_stack([np.ones(len(y))] + cols)
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ b
    k = np.linalg.matrix_rank(X)
    se = np.sqrt(np.diag(np.linalg.pinv(X.T @ X)) * (res @ res / max(len(y) - k, 1)))
    return b, b / se


def report(basket, meta):
    joined = {z: v for z, v in basket.items() if z in meta}
    print(f"basket ZIPs: {len(basket)}   joined to demographics: {len(joined)}")
    if not joined:
        sys.exit("no basket ZIP matched the national milk file — check the zip column")
    items = sorted({i for v in joined.values() for i in v})
    print(f"items: {items}\n")

    # --- 1. Dispersion, the headline test -------------------------------------
    print("=== 1. Dispersion by item (the headline test) ===")
    print(f"  {'item':<18}{'n':>5}{'mean $':>9}{'sd $':>9}{'CV':>8}{'IQR $':>9}{'distinct':>10}")
    cv = {}
    for it in items:
        v = [d[it] for d in joined.values() if it in d]
        if len(v) < 20:
            continue
        s, m = np.std(v), np.mean(v)
        cv[it] = 100 * s / m
        print(f"  {it:<18}{len(v):>5}{m:>9.2f}{s:>9.3f}{cv[it]:>7.1f}%"
              f"{np.percentile(v, 75) - np.percentile(v, 25):>9.2f}{len(set(v)):>10}")
    k = [cv[i] for i in cv if i in KVI]
    p = [cv[i] for i in cv if i in PANTRY]
    if k and p:
        print(f"\n  mean CV — traffic drivers {np.mean(k):.1f}%   pantry {np.mean(p):.1f}%"
              f"   ratio {np.mean(k) / max(np.mean(p), 1e-9):.2f}x")
        print("  -> a large ratio supports a category carve-off for milk/KVIs.")

    # --- 2. Within-state dispersion (strips the coarse geographic component) ---
    print("\n=== 2. Within-state dispersion ===")
    print(f"  {'item':<18}{'mean within-state sd':>22}{'states':>9}")
    for it in items:
        by = defaultdict(list)
        for z, d in joined.items():
            if it in d:
                by[meta[z]["st"]].append(d[it])
        sds = [np.std(v) for v in by.values() if len(v) >= 10]
        if sds:
            print(f"  {it:<18}{np.mean(sds):>22.3f}{len(sds):>9}")

    # --- 3. Urban-rural gap ----------------------------------------------------
    print("\n=== 3. Urban minus rural, by item ===")
    for it in items:
        u = [d[it] for z, d in joined.items() if it in d and meta[z]["geo"] == "urban"]
        r = [d[it] for z, d in joined.items() if it in d and meta[z]["geo"] == "rural"]
        if len(u) >= 10 and len(r) >= 10:
            print(f"  {it:<18}{np.mean(u) - np.mean(r):>+9.3f}  "
                  f"({100 * (np.mean(u) - np.mean(r)) / np.mean(r):+.1f}%)")

    # --- 4. Racial gradient, item by item --------------------------------------
    print("\n=== 4. %Black gradient by item (rural; income + log pop controlled) ===")
    for it in items:
        Z = [z for z, d in joined.items() if it in d and meta[z]["geo"] == "rural"]
        if len(Z) < 30:
            continue
        y = np.array([joined[z][it] for z in Z])
        b, t = ols([np.array([meta[z]["blk"] for z in Z]),
                    np.array([meta[z]["inc"] for z in Z]) / 1000,
                    np.log(np.array([meta[z]["pop"] for z in Z]))], y)
        print(f"  {it:<18} n={len(Z):>4}  {b[1]:+.5f} (t {t[1]:+.2f})")

    # --- 5. THE WITHIN-STORE PLACEBO ------------------------------------------
    print("\n=== 5. Within-store placebo: milk relative to the pantry basket ===")
    print("  log(milk) - mean log(pantry items), at the SAME store, on %Black.")
    print("  Every store-level confound differences out.")
    print("  Coefficients are in LOG points per percentage point of %Black;")
    print("  the $ column converts at the sample mean milk price.")
    pan = [i for i in items if i in PANTRY]
    if not pan or "whole_milk" not in items:
        print("  -- needs whole_milk plus at least one pantry item; not available")
        return
    Z, y = [], []
    for z, d in joined.items():
        have = [i for i in pan if i in d and d[i] > 0]
        if "whole_milk" in d and d["whole_milk"] > 0 and len(have) >= 2:
            Z.append(z)
            y.append(math.log(d["whole_milk"]) - np.mean([math.log(d[i]) for i in have]))
    y = np.array(y)
    print(f"  stores with milk and >=2 pantry items: {len(Z)}")
    if len(Z) < 30:
        print("  -- too few for inference")
        return
    for lab, sub in (("all stores", Z),
                     ("rural only", [z for z in Z if meta[z]["geo"] == "rural"]),
                     ("urban only", [z for z in Z if meta[z]["geo"] == "urban"])):
        if len(sub) < 30:
            continue
        idx = [Z.index(z) for z in sub]
        b, t = ols([np.array([meta[z]["blk"] for z in sub]),
                    np.array([meta[z]["inc"] for z in sub]) / 1000,
                    np.log(np.array([meta[z]["pop"] for z in sub]))], y[idx])
        mm = np.mean([joined[z]["whole_milk"] for z in sub])
        print(f"    {lab:<12} n={len(sub):>4}  {b[1]:+.5f} log-pts (t {t[1]:+.2f})"
              f"   = ${b[1] * mm:+.4f}/gal per pt, ${b[1] * mm * 20:+.3f} over a 20-pt gap")
    sts = sorted({meta[z]["st"] for z in Z})
    if len(sts) > 1:
        D = [np.array([1.0 if meta[z]["st"] == s else 0.0 for z in Z]) for s in sts[1:]]
        b, t = ols([np.array([meta[z]["blk"] for z in Z]),
                    np.array([meta[z]["inc"] for z in Z]) / 1000,
                    np.log(np.array([meta[z]["pop"] for z in Z]))] + D, y)
        mm = np.mean([joined[z]["whole_milk"] for z in Z])
        print(f"    {'+ state FE':<12} n={len(Z):>4}  {b[1]:+.5f} log-pts (t {t[1]:+.2f})"
              f"   = ${b[1] * mm:+.4f}/gal per pt, ${b[1] * mm * 20:+.3f} over a 20-pt gap")


def selftest():
    """Synthetic basket with a KNOWN answer, to verify the code path end to end.

    Construction: pantry items are near-uniform; milk carries a real +$0.004/pt
    %Black gradient. A correct run recovers the right sign and significance.

    Expect partial attenuation: the synthetic DGP includes an urban term that
    the regression does not (it controls income and log-population instead),
    and %Black correlates with urbanicity in the real demographics used for the
    covariates. That is honest omitted-variable attenuation in the fixture, not
    bias in the estimator.
    """
    meta = load_meta()
    rng = np.random.default_rng(0)
    zips = list(meta)[:1200]
    rows = [["zip", "item", "price"]]
    for z in zips:
        m = meta[z]
        base = 3.0 + 0.4 * (m["st"] in ("LA", "PA", "CA"))
        milk = base + 0.004 * m["blk"] - 0.35 * (m["geo"] == "urban") + rng.normal(0, 0.15)
        rows.append([z, "whole_milk", round(max(milk, 0.5), 2)])
        for it, lvl in (("flour_5lb", 2.48), ("green_beans_can", 0.98), ("ketchup_20oz", 1.62)):
            rows.append([z, it, round(lvl + rng.normal(0, 0.01), 2)])
    path = "/tmp/_selftest_basket.csv"
    with open(path, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    print("SELFTEST — synthetic basket: pantry flat, milk carries a +0.004/pt %Black slope")
    print("Section 5 should recover roughly +0.004.\n")
    report(load_basket(path), meta)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        selftest()
    elif len(sys.argv) > 1:
        report(load_basket(sys.argv[1]), load_meta())
    else:
        sys.exit(__doc__)
