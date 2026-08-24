"""Collect a multi-item basket across South Carolina Walmart stores.

Answers: does Walmart's store-to-store price variation extend beyond fluid milk?
The Aldi panel (reports/dairy_pattern.md) says one price decision per store drives
the whole refrigerated fluid-milk case while 13 of 20 other products carry a single
statewide price. This tests whether Walmart behaves the same way.

Requires BRIGHTDATA_API_TOKEN in the environment. Set it as an environment
variable — never on the command line or in a file.

    export BRIGHTDATA_API_TOKEN=...
    python3 analysis/collect_sc_basket.py --resolve      # find SKUs, review them
    python3 analysis/collect_sc_basket.py --dry-run      # plan, no network
    python3 analysis/collect_sc_basket.py --limit 5      # smoke test, 5 stores
    python3 analysis/collect_sc_basket.py                # full run

Writes data/walmart_basket_sc.csv in the long layout analysis/basket_test.py reads.
Every row is store-verified; unverifiable rows are dropped and counted, never
written with a proxy-exit price.
"""
import csv
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from milk_pricing.sources.walmart_basket import (  # noqa: E402
    Rejected, StoreMismatch, collect, fetch_pinned, resolve_skus)

OUT = "data/walmart_basket_sc.csv"

# Known item ids, recovered from the Sacramento catalogue in walmart_milk_raw.json.
KNOWN = {
    "whole_milk":      {"sku": "10450114", "size_fl_oz": 128.0, "tier": "fluid milk"},
    "milk_1pct_gal":   {"sku": "10450116", "size_fl_oz": 128.0, "tier": "fluid milk"},
    "chocolate_milk":  {"sku": "17248403", "size_fl_oz": 128.0, "tier": "fluid milk"},
}

# Item ids unknown — resolved by search, then reviewed before collecting.
# Ordered by value per reports/dairy_pattern.md section 6: items OUTSIDE the
# refrigerated fluid-milk case carry the information.
TO_RESOLVE = [
    ("cottage_cheese",  "great value small curd cottage cheese 24 oz", "zero-variance dairy"),
    ("greek_yogurt",    "great value nonfat plain greek yogurt 32 oz", "zero-variance dairy"),
    ("mozzarella",      "great value shredded mozzarella cheese 8 oz", "zero-variance dairy"),
    ("sour_cream",      "great value sour cream 16 oz",                "zero-variance dairy"),
    ("butter_sticks",   "great value salted sweet cream butter sticks 16 oz", "butter & eggs"),
    ("eggs_12ct",       "great value large white eggs 12 count",       "butter & eggs"),
    ("white_bread",     "great value white sandwich bread 20 oz",      "traffic driver"),
    ("flour_5lb",       "great value all purpose flour 5 lb",          "pantry"),
    ("green_beans_can", "great value cut green beans 14.5 oz",         "pantry"),
    ("veg_oil_48oz",    "great value vegetable oil 48 oz",             "pantry"),
]


def sc_zips(limit=None):
    """The 92 SC store ZIPs already covered by the milk file, metro-first so a
    truncated run still spans both price bands."""
    rows = [r for r in csv.DictReader(open("data/sc_walmart_official.csv")) if r["whole_milk"]]
    rows.sort(key=lambda r: (r["geo"] != "urban", r["zip"]))
    z = [r["zip"].zfill(5) for r in rows]
    return z[:limit] if limit else z


def main(argv):
    limit = None
    if "--limit" in argv:
        limit = int(argv[argv.index("--limit") + 1])
    zips = sc_zips(limit)
    dry = "--dry-run" in argv
    token = os.environ.get("BRIGHTDATA_API_TOKEN")

    if not dry and not token:
        sys.exit("BRIGHTDATA_API_TOKEN is not set.\n"
                 "  export BRIGHTDATA_API_TOKEN=...   (env var only, never a flag or a file)\n"
                 "Run with --dry-run to see the plan without it.")

    if "--resolve" in argv:
        print("Resolving item ids by search. REVIEW THESE before collecting — a search for a\n"
              "private-label staple returns third-party listings alongside the shelf item.\n")
        for col, query, tier in TO_RESOLVE:
            print(f"{col}  ({tier})   query: {query!r}")
            if dry:
                print("    [dry run]")
                continue
            try:
                for sku, name in resolve_skus(query, token):
                    print(f"    {sku:<14} {name[:80]}")
            except Exception as e:
                print(f"    failed: {e}")
        print("\nPaste the chosen ids into KNOWN at the top of this file, then re-run.")
        return

    plan = dict(KNOWN)
    print(f"stores: {len(zips)}   items: {len(plan)}   requests: {len(zips) * len(plan)}"
          f"   (at ~1 s pacing, about {len(zips) * len(plan) / 60:.0f} min)")
    print(f"items: {', '.join(plan)}")
    unresolved = [c for c, _, _ in TO_RESOLVE if c not in plan]
    if unresolved:
        print(f"\nNOT being collected — ids unresolved: {', '.join(unresolved)}")
        print("These are the informative ones. Run --resolve first.")
    if dry:
        print(f"\n[dry run] would write {OUT}")
        print(f"[dry run] first 5 ZIPs: {zips[:5]}")
        return

    errs = Counter()
    ok = []

    def on_row(r):
        print(f"  ok  {r['requested_zip']}  {r['item']:<16} ${r['price']:.2f}  "
              f"store {r.get('store_id')}")

    def on_error(z, col, e):
        errs[type(e).__name__] += 1
        print(f"  --  {z}  {col:<16} {type(e).__name__}: {e}")

    ok = collect(plan, zips, token, on_row=on_row, on_error=on_error)

    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["zip", "item", "price", "store_id", "city", "state", "pinned_via"])
        for r in ok:
            w.writerow([r["requested_zip"], r["item"], r["price"], r.get("store_id"),
                        r.get("city"), r.get("state"), r.get("pinned_via")])
    print(f"\nwrote {len(ok)} verified rows to {OUT}")
    print(f"dropped: {dict(errs)}")
    if ok:
        print(f"pinning strategies that worked: {Counter(r['pinned_via'] for r in ok).most_common()}")
    print(f"\nnext: python3 analysis/basket_test.py {OUT} --describe")


if __name__ == "__main__":
    main(sys.argv[1:])
