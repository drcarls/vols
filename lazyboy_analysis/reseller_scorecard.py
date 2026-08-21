"""Each retailer's shelf, brand by brand, against what the maker offers.

`channel_depth.py` reads maker-first: one brand, then the shops carrying it.
This reads shop-first, which is how a buyer sees it -- for one store, every
brand on the floor, how much of each maker's line it represents, and what that
selection looks like on price, features and materials.

Where a maker's own catalogue could not be collected the line-share column is
blank rather than guessed; the shelf figures still stand on their own.
"""

import csv
import json
import argparse
import statistics as st
from collections import defaultdict

from assortment import load, load_descriptions, own_store_category

CATS = ("Recliners", "Motion sofas")


def maker_lines(manufacturers, covers):
    """Model count per brand and category, from each maker's own catalogue."""
    out = defaultdict(dict)
    for brand, rec in json.loads(open(manufacturers).read()).items():
        if rec.get("source") == "unavailable":
            continue
        for cat, n in rec.get("models", {}).items():
            key = "Motion sofas" if cat.startswith(("Motion", "Sofas (action")) else cat
            if key in CATS:
                out[brand][key] = out[brand].get(key, 0) + n

    lz = defaultdict(set)
    for r in csv.DictReader(open(covers)):
        cat = own_store_category(r["product"])
        if cat in CATS:
            lz[cat].add(r["product"])
    for cat, models in lz.items():
        out["La-Z-Boy"][cat] = len(models)
    return out


def main(a):
    rows = load(a.skus, load_descriptions())
    lines = maker_lines(a.manufacturers, a.covers)

    for ret in ("slumberland", "steinhafels"):
        for cat in CATS:
            sub = [r for r in rows if r["retailer"] == ret and r["cat"] == cat]
            if not sub:
                continue
            by = defaultdict(list)
            for r in sub:
                by[r["brand"]].append(r)
            total_sku = len(sub)
            total_mdl = len({r["product_id"] for r in sub})

            print(f"\n{'=' * 108}")
            print(f"{ret.upper()}  ·  {cat}  —  {total_mdl} models / {total_sku} SKUs "
                  f"across {len(by)} brands")
            print("=" * 108)
            print(f"{'brand':<24}{'models':>7}{'SKUs':>6}{'shelf':>7}"
                  f"{'maker line':>12}{'% of line':>11}{'median $':>10}"
                  f"{'feats':>7}{'leather':>13}")
            print("-" * 108)

            for b, v in sorted(by.items(), key=lambda kv: -len(kv[1])):
                if len(v) < a.min_n:
                    continue
                mdl = len({x["product_id"] for x in v})
                line = lines.get(b, {}).get(cat)
                # Leather share over the whole shelf, never over the subset whose
                # material is named. Listings name leather far more reliably than
                # fabric, so a share taken over named-only runs high -- it read
                # Southern Motion as 100% leather off 14 named SKUs. Over the
                # shelf, every brand sits on the same denominator: exact for
                # La-Z-Boy, whose cover codes validate the convention, and a
                # floor for the rest, where unnamed leather would be missed.
                lea = sum(1 for x in v if x["mat"] == "Leather") / len(v) * 100
                print(f"{b:<24}{mdl:>7}{len(v):>6}{len(v)/total_sku*100:>6.0f}%"
                      f"{(line or '—'):>12}"
                      f"{(f'{mdl/line*100:.0f}%' if line else '—'):>11}"
                      f"{st.median([x['price'] for x in v]):>10,.0f}"
                      f"{st.mean([x['feats'] for x in v]):>7.1f}"
                      f"{lea:>12.0f}%{'' if b == 'La-Z-Boy' else '*'}")

    print(f"\n\n  shelf  = share of this store's SKUs in this category")
    print(f"  % of line = models carried, over the models the maker lists itself")
    print(f"  leather   = leather share of this shelf. Exact for La-Z-Boy, whose cover")
    print(f"              codes validate its naming convention; * marks a floor,")
    print(f"              where a listing that never names leather cannot show it.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--skus", default="data/skus.csv")
    ap.add_argument("--covers", default="data/lazboy_covers.csv")
    ap.add_argument("--manufacturers", default="data/manufacturers.json")
    ap.add_argument("--min-n", type=int, default=6)
    ap.add_argument("--min-material", type=int, default=6,
                    help="identified-material SKUs needed before reporting a share")
    main(ap.parse_args())
