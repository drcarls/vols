"""Who sits immediately below and immediately above a brand's price band.

Two different questions, answered separately because they can disagree:

  * Structural position -- each brand's median price in the same store and
    category, indexed to the focus brand. Says who is broadly cheaper or
    dearer.
  * Adjacency -- for the focus brand's own SKUs, how many competitor models
    sit within one step below versus one step above. Says who is actually
    lined up next to it on the floor, which a median can hide when two brands
    overlap across a wide range.
"""

import csv
import argparse
import statistics as st
from collections import defaultdict

SEATING = {"Recliner", "Sofa", "Loveseat", "Sectional"}
MIN_N = 5


def load(path):
    rows = []
    for r in csv.DictReader(open(path)):
        if r["form"] not in SEATING:
            continue
        r["price"] = float(r["price"])
        rows.append(r)
    return rows


def price_index(rows, focus):
    print(f"=== STRUCTURAL POSITION: median price, {focus} = 100 ===\n")
    for ret in ("slumberland", "steinhafels"):
        forms = sorted({r["form"] for r in rows if r["retailer"] == ret})
        print(f"-- {ret} --")
        header = f"{'brand':<24}" + "".join(f"{f:>13}" for f in forms)
        print(header)
        print("-" * len(header))

        med = defaultdict(dict)
        for f in forms:
            for b in {r["brand"] for r in rows}:
                v = [r["price"] for r in rows
                     if r["retailer"] == ret and r["form"] == f and r["brand"] == b]
                if len(v) >= MIN_N:
                    med[b][f] = st.median(v)

        base = med.get(focus, {})
        ordered = sorted(med, key=lambda b: -st.mean(
            [med[b][f] / base[f] for f in med[b] if f in base] or [0]))
        for b in ordered:
            cells = ""
            for f in forms:
                if f in med[b] and f in base:
                    cells += f"{med[b][f] / base[f] * 100:>12.0f} "
                elif f in med[b]:
                    cells += f"{'(' + format(med[b][f], ',.0f') + ')':>13}"
                else:
                    cells += f"{'-':>13}"
            mark = "  <<<" if b == focus else ""
            print(f"{b:<24}{cells}{mark}")
        print()
    print("  Values are the brand's median as a percentage of the focus brand's,")
    print("  same store and category. A figure in (parentheses) is that brand's")
    print("  own median where the focus brand has too few SKUs to index against.\n")


def adjacency(rows, focus, window):
    """For each focus SKU, which competitor models sit one step below vs above."""
    peers = defaultdict(list)
    for r in rows:
        if r["brand"] != focus:
            peers[(r["retailer"], r["form"])].append(r)

    below, above = defaultdict(set), defaultdict(set)
    n_focus = 0
    for r in rows:
        if r["brand"] != focus:
            continue
        n_focus += 1
        p = r["price"]
        lo, hi = p * (1 - window / 100), p * (1 + window / 100)
        for x in peers[(r["retailer"], r["form"])]:
            pair = (r["retailer"], r["product"], x["brand"], x["product_id"])
            if lo <= x["price"] < p:
                below[x["brand"]].add(pair)
            elif p < x["price"] <= hi:
                above[x["brand"]].add(pair)

    print(f"=== ADJACENCY: competitor models within {window:.0f}% of a {focus} SKU ===\n")
    print(f"    ({n_focus} {focus} seating SKUs; counts are distinct model pairs)\n")
    print(f"{'brand':<24}{'BELOW':>9}{'ABOVE':>9}{'net':>9}   position")
    print("-" * 68)
    brands = sorted(set(below) | set(above),
                    key=lambda b: -(len(below[b]) + len(above[b])))
    for b in brands:
        lo, hi = len(below[b]), len(above[b])
        if lo + hi < 10:
            continue
        share = lo / (lo + hi) * 100
        if share >= 65:
            pos = "undercuts"
        elif share <= 35:
            pos = "sits above"
        else:
            pos = "interleaved"
        print(f"{b:<24}{lo:>9}{hi:>9}{hi - lo:>+9}   {pos} ({share:.0f}% of adjacency is below)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--skus", default="data/skus.csv")
    ap.add_argument("--brand", default="La-Z-Boy")
    ap.add_argument("--window", type=float, default=30.0)
    args = ap.parse_args()
    rows = load(args.skus)
    price_index(rows, args.brand)
    adjacency(rows, args.brand, args.window)
