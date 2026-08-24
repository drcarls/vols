"""Walmart cross-store dispersion by product: is fluid milk the exception?

Collected 2026-08-24 via the Bright Data "Walmart - products" dataset
(gd_l95fol7l1ru6rlo116). Reproduces reports/walmart_basket_national.md.

COLLECTION NOTE — why this is a national random sample and not South Carolina.
Three store-pinning mechanisms were tested against this Bright Data account and
all three failed:
  * Web Unlocker /request with a `zip` parameter -> empty response; not a valid
    field for this zone. `state` likewise.
  * URL params (?storeId=, ?athstid=, ?location=) and store cookies
    (locGuestData, ASSORTMENT_STORE_ID) -> ignored; successive requests resolved
    to Sacramento, Nashville and Ashburn regardless.
  * Dataset API with a `zipcode` input field -> silently dropped, not echoed
    back; identical inputs returned Sacramento twice and Saginaw once.
The account holds one zone (`unblocker`, no geo targeting), so the serving store
is set by the scraper's exit IP and cannot be chosen. What it CAN do is return
the store it actually hit, in `store_id` / `store_location`. Repeating a URL with
a distinct cache-busting query param (?cb=N) defeats the dataset's URL
deduplication and draws a fresh random store each time.

That yields a random national sample of real, identified stores — enough for a
dispersion comparison ACROSS products, which is the question here, but not for a
South Carolina analysis.
"""
import csv
from collections import Counter, defaultdict

import numpy as np

SRC = "data/walmart_basket_national.csv"
TIER_ORDER = ("fluid milk", "traffic driver", "butter/eggs", "other dairy", "pantry")


def load():
    rows = list(csv.DictReader(open(SRC)))
    for r in rows:
        r["price"] = float(r["price"])
    return rows


def main():
    rows = load()
    byitem = defaultdict(list)
    tier = {}
    for r in rows:
        byitem[r["item"]].append(r["price"])
        tier[r["item"]] = r["tier"]
    print(f"observations: {len(rows)}   distinct stores: {len({r['store_id'] for r in rows})}")

    print("\n=== Dispersion across distinct stores, by item ===")
    print(f"  {'item':<17}{'tier':<15}{'stores':>7}{'mean $':>9}{'sd $':>8}{'CV':>7}"
          f"{'distinct':>9}{'range':>16}")
    stats = []
    for it, v in sorted(byitem.items(), key=lambda kv: -np.std(kv[1]) / np.mean(kv[1])):
        cv = 100 * np.std(v) / np.mean(v)
        stats.append((it, tier[it], len(v), cv, len(set(v))))
        print(f"  {it:<17}{tier[it]:<15}{len(v):>7}{np.mean(v):>9.2f}{np.std(v):>8.3f}"
              f"{cv:>6.1f}%{len(set(v)):>9}{f'${min(v):.2f}-${max(v):.2f}':>16}")

    print("\n=== Grouped by tier ===")
    for t in TIER_ORDER:
        g = [s for s in stats if s[1] == t]
        if not g:
            continue
        print(f"  {t:<16} {len(g)} items   mean CV {np.mean([s[3] for s in g]):5.1f}%   "
              f"median distinct prices {np.median([s[4] for s in g]):.0f}")

    print("\n=== Within-store: stores that drew the full basket ===")
    byst = defaultdict(dict)
    for r in rows:
        byst[r["store_id"]][r["item"]] = r["price"]
    full = {s: v for s, v in byst.items() if len(v) >= 12}
    if len(full) >= 2:
        ids = sorted(full, key=lambda s: -len(full[s]))[:2]
        loc = {s: next(r["store_location"] for r in rows if r["store_id"] == s) for s in ids}
        items = sorted(set(full[ids[0]]) & set(full[ids[1]]))
        print(f"  {'item':<17}{loc[ids[0]][:22]:>24}{loc[ids[1]][:22]:>24}{'diff':>9}")
        same = 0
        for it in sorted(items, key=lambda i: abs(full[ids[0]][i] - full[ids[1]][i])):
            a, b = full[ids[0]][it], full[ids[1]][it]
            if abs(a - b) < 0.005:
                same += 1
            print(f"  {it:<17}{a:>24.2f}{b:>24.2f}{a-b:>+9.2f}")
        print(f"  -> identical to the cent: {same}/{len(items)}")

    print("\n=== Highest-priced milk stores ===")
    wm = sorted([r for r in rows if r["item"] == "whole_milk"], key=lambda r: -r["price"])[:6]
    for r in wm:
        print(f"  ${r['price']:>5.2f}  {r['store_location']}")
    print("  (Pennsylvania's Milk Marketing Board sets minimum RETAIL milk prices — "
          "see reports/walmart_pricing_geography.md)")


if __name__ == "__main__":
    main()
