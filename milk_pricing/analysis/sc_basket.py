"""The full 13-item Great Value basket across all 92 South Carolina Walmart stores.

Collected via Bright Data's "Walmart - products zipcodes" scraper
(gd_m693oc1r1gebnayxq), resolving by `zip_code` alone — `store_id` was omitted
because the IDs in sc_walmart_official.csv do not always match the ones Bright
Data resolves for a ZIP, which cost 18 of 92 stores on the previous run.

READ THIS BEFORE USING THE PRICES. Every record from this scraper carries
`promotion_fulltext: "Price when purchased online"`. On the single-item SC run,
56 of 74 priced records sat at the $3.52 national default, correlation with the
known SC shelf price was r = +0.178, and 0 of 74 matched it. So this measures
Walmart's ONLINE price in South Carolina, not the shelf price. It is a real
object and worth having, but it is not the series the retail theory needs.
See reports/brightdata_zipcode_trap.md.

Usage:  python3 analysis/sc_basket.py            # after data/sc_basket.csv exists
        python3 analysis/sc_basket.py --build    # convert the raw snapshot first
"""
import csv
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

RAW = "/tmp/sc_basket_raw.json"
OUT = "data/sc_basket.csv"
META = "/tmp/scbasket.json"
TIER_ORDER = ("fluid milk", "traffic driver", "butter/eggs", "other dairy", "pantry")


def build():
    meta = json.load(open(META))
    inv = {v: k for k, v in meta["items"].items()}
    tiers = meta["tiers"]
    ref = {r["zip"].zfill(5): r for r in csv.DictReader(open("data/sc_walmart_official.csv"))
           if r["whole_milk"]}
    d = json.load(open(RAW))
    n = 0
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["zip", "item", "tier", "price", "store_resolved", "promo_label",
                    "known_shelf_milk", "county", "pct_black", "median_income", "geo"])
        for x in d:
            url = str(x.get("url") or "")
            sku = next((s for s in inv if s in url), None)
            z = str(x.get("zip_code") or "").zfill(5)
            if not sku or z not in ref or not x.get("final_price"):
                continue
            col = inv[sku]
            r = ref[z]
            w.writerow([z, col, tiers[col], x["final_price"], x.get("pickup_address"),
                        x.get("promotion_fulltext"), r["whole_milk"], r["county"],
                        r["pct_black"], r["median_income"], r["geo"]])
            n += 1
    print(f"wrote {OUT}: {n} rows from {len(d)} raw records")


def ols(cols, y):
    X = np.column_stack([np.ones(len(y))] + cols)
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ b
    k = np.linalg.matrix_rank(X)
    se = np.sqrt(np.diag(np.linalg.pinv(X.T @ X)) * (res @ res / max(len(y) - k, 1)))
    return b, b / se


def main():
    rows = list(csv.DictReader(open(OUT)))
    for r in rows:
        r["price"] = float(r["price"])
        r["blk"] = float(r["pct_black"])
        r["inc"] = float(r["median_income"])
    print(f"rows {len(rows)}   items {len({r['item'] for r in rows})}   "
          f"SC stores {len({r['zip'] for r in rows})}")
    lab = Counter(r["promo_label"] for r in rows).most_common(2)
    print(f"  price labels: {lab}")

    byitem = defaultdict(list)
    tier = {}
    for r in rows:
        byitem[r["item"]].append(r)
        tier[r["item"]] = r["tier"]

    print("\n=== Dispersion across SC stores, by item ===")
    print(f"  {'item':<17}{'tier':<15}{'n':>5}{'mean':>8}{'sd':>8}{'CV':>7}{'distinct':>9}"
          f"{'modal share':>13}{'range':>16}")
    stats = []
    for it, v in sorted(byitem.items(), key=lambda kv: -np.std([x["price"] for x in kv[1]])
                        / max(np.mean([x["price"] for x in kv[1]]), 1e-9)):
        p = [x["price"] for x in v]
        cv = 100 * np.std(p) / np.mean(p)
        modal = Counter(p).most_common(1)[0][1] / len(p)
        stats.append((it, tier[it], cv, len(set(p))))
        print(f"  {it:<17}{tier[it]:<15}{len(p):>5}{np.mean(p):>8.2f}{np.std(p):>8.3f}{cv:>6.1f}%"
              f"{len(set(p)):>9}{100*modal:>12.0f}%{f'${min(p):.2f}-${max(p):.2f}':>16}")

    print("\n=== By tier ===")
    for t in TIER_ORDER:
        g = [s for s in stats if s[1] == t]
        if g:
            print(f"  {t:<16} {len(g)} items   mean CV {np.mean([s[2] for s in g]):5.1f}%   "
                  f"median distinct {np.median([s[3] for s in g]):.0f}")

    print("\n=== %Black gradient per item (income controlled) — the actual question ===")
    for it, v in sorted(byitem.items()):
        if len(v) < 30:
            continue
        b, t = ols([np.array([x["blk"] for x in v]), np.array([x["inc"] for x in v]) / 1000],
                   np.array([x["price"] for x in v]))
        flag = "  <-- p<.05" if abs(t[1]) > 1.98 else ""
        print(f"  {it:<17}{tier[it]:<15} n={len(v):>3}  {b[1]:+.5f} (t {t[1]:+.2f}){flag}")

    milk = [r for r in rows if r["item"] == "whole_milk"]
    if milk:
        bd = np.array([r["price"] for r in milk])
        kn = np.array([float(r["known_shelf_milk"]) for r in milk])
        print(f"\n=== Sanity: this scraper vs the known SC shelf price (whole milk, n={len(milk)}) ===")
        print(f"  correlation r = {np.corrcoef(bd, kn)[0, 1]:+.3f}   "
              f"exact matches {int(sum(abs(bd-kn) < 0.02))}/{len(milk)}")
        b, t = ols([np.array([r["blk"] for r in milk]), np.array([r["inc"] for r in milk]) / 1000], kn)
        print(f"  known shelf price on %Black: {b[1]:+.5f} (t {t[1]:+.2f})  <- the clean series")


if __name__ == "__main__":
    if "--build" in sys.argv:
        build()
    if not os.path.exists(OUT):
        sys.exit(f"{OUT} not found — run with --build once the snapshot is downloaded")
    main()
