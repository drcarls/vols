"""What each maker offers, against what each dealer actually stocks.

Reads three sources and puts them in one frame: manufacturer catalogues
(`manufacturers.json`), La-Z-Boy's own store at cover level
(`lazboy_covers.csv`), and the dealer feeds (`skus.csv`).

Two cautions the numbers do not carry on their own. Manufacturer feeds list
models, not colourways, so a maker's SKU column is blank unless the feed
exposes variants -- a dealer's higher SKU count never means it offers more
choice than the maker. And the coverage percentages divide a dealer's model
count by the maker's, which is only a fair ratio where the maker's figure is a
real catalogue rather than a sample.
"""

import csv
import json
import re
import argparse
import statistics as st
from collections import defaultdict

from assortment import category, own_store_category
from teeup import ACCESSORY_RE

CATS = ("Recliners", "Motion sofas")


def dealer_counts(path):
    out = defaultdict(lambda: defaultdict(lambda: {"skus": 0, "models": set()}))
    for r in csv.DictReader(open(path)):
        if ACCESSORY_RE.search(r["product"]):
            continue
        cat = category(r)
        if not cat:
            continue
        cell = out[r["brand"]][(r["retailer"], cat)]
        cell["skus"] += 1
        cell["models"].add(r["product_id"])
    return out


def lazboy_own(path):
    models, covers = defaultdict(set), defaultdict(int)
    for r in csv.DictReader(open(path)):
        cat = own_store_category(r["product"])
        if not cat:
            continue
        models[cat].add(r["product"])
        covers[cat] += 1
    return models, covers


def main(a):
    makers = json.loads(open(a.manufacturers).read())
    dealers = dealer_counts(a.skus)
    lz_models, lz_covers = lazboy_own(a.covers)

    print("=" * 100)
    print("MAKER'S OWN CATALOGUE vs WHAT EACH DEALER STOCKS".center(100))
    print("=" * 100)

    brands = ["La-Z-Boy", "Flexsteel", "Southern Motion", "Franklin",
              "Ashley", "Best Home Furnishings", "Jackson/Catnapper", "Bassett"]
    for brand in brands:
        rows = []
        if brand == "La-Z-Boy":
            src = "own store, scraped"
            for cat in CATS:
                rows.append((cat, len(lz_models[cat]), lz_covers[cat]))
        elif brand in makers and makers[brand].get("source") != "unavailable":
            src = makers[brand]["source"]
            m = makers[brand]["models"]
            sk = makers[brand].get("skus", {})
            for cat in CATS:
                keys = [k for k in m if k == cat or (cat == "Motion sofas"
                        and k.startswith("Sofas (action"))]
                if keys:
                    rows.append((m and keys[0], sum(m[k] for k in keys),
                                 sum(sk.get(k, 0) for k in keys)))
        else:
            reason = makers.get(brand, {}).get("reason", "not collected")
            print(f"\n-- {brand} --")
            print(f"   own site: unavailable ({reason})")
            for ret in ("slumberland", "steinhafels"):
                for cat in CATS:
                    d = dealers[brand].get((ret, cat))
                    if d:
                        print(f"   {ret:<14}{cat:<28}"
                              f"{len(d['models']):>4} models  {d['skus']:>4} SKUs")
            continue

        print(f"\n-- {brand}  ({src}) --")
        print(f"   {'channel':<16}{'category':<28}{'models':>8}{'SKUs':>7}"
              f"{'per model':>11}{'% of maker line':>17}")
        for label, mdl, sku in rows:
            per = f"{sku/mdl:.1f}" if sku and mdl else "-"
            print(f"   {'MAKER':<16}{str(label):<28}{mdl:>8}"
                  f"{(sku or '-'):>7}{per:>11}{'':>17}")
            cat = "Motion sofas" if str(label).startswith(("Motion", "Sofas")) else label
            for ret in ("slumberland", "steinhafels"):
                d = dealers[brand].get((ret, cat))
                if not d:
                    continue
                dm = len(d["models"])
                print(f"   {ret:<16}{cat:<28}{dm:>8}{d['skus']:>7}"
                      f"{d['skus']/dm:>11.1f}{dm/mdl*100:>16.0f}%")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--skus", default="data/skus.csv")
    ap.add_argument("--covers", default="data/lazboy_covers.csv")
    ap.add_argument("--manufacturers", default="data/manufacturers.json")
    main(ap.parse_args())
