"""Summarise the cross-retailer catalogue.

Every comparison here is run within a single retailer wherever possible. Brands
are stocked in different mixes at different stores, so pooling the two would let
assortment differences masquerade as positioning differences.
"""

import csv
import argparse
import statistics as st
from collections import defaultdict, Counter

SEATING = {"Recliner", "Sofa", "Loveseat", "Sectional"}
MIN_N = 6


def load(path):
    rows = []
    for r in csv.DictReader(open(path)):
        r["price"] = float(r["price"])
        rows.append(r)
    return rows


def table(title, header, lines):
    print(f"\n=== {title} ===\n")
    print(header)
    print("-" * len(header))
    for ln in lines:
        print(ln)


def coverage(rows):
    bx = defaultdict(Counter)
    for r in rows:
        bx[r["brand"]][r["retailer"]] += 1
    lines = []
    for b in sorted(bx, key=lambda b: -sum(bx[b].values())):
        s, t = bx[b]["slumberland"], bx[b]["steinhafels"]
        lines.append(f"{b:<24}{s:>13}{t:>13}{s + t:>8}")
    table("BRAND COVERAGE (all categories)",
          f"{'brand':<24}{'slumberland':>13}{'steinhafels':>13}{'total':>8}", lines)


def positioning(rows):
    for ret in ("slumberland", "steinhafels"):
        g = defaultdict(list)
        for r in rows:
            if r["retailer"] == ret and r["form"] in SEATING:
                g[r["brand"]].append(r["price"])
        lines = [f"{b:<24}{len(v):>6}{st.median(v):>12,.0f}{st.mean(v):>11,.0f}"
                 for b, v in sorted(g.items(), key=lambda kv: -st.median(kv[1]))
                 if len(v) >= MIN_N]
        table(f"PRICE POSITIONING WITHIN {ret.upper()} (upholstered seating)",
              f"{'brand':<24}{'n':>6}{'median':>12}{'mean':>11}", lines)


def by_form(rows):
    g = defaultdict(list)
    for r in rows:
        if r["form"] in SEATING:
            g[(r["brand"], r["form"])].append(r["price"])
    lines = [f"{b:<24}{f:<12}{len(v):>6}{st.median(v):>12,.0f}"
             for (b, f), v in sorted(g.items(), key=lambda kv: -st.median(kv[1]))
             if len(v) >= MIN_N]
    table("BRAND x FORM (both retailers pooled)",
          f"{'brand':<24}{'form':<12}{'n':>6}{'median':>12}", lines)


def discounting(rows):
    g = defaultdict(list)
    tot = Counter()
    for r in rows:
        if r["form"] not in SEATING:
            continue
        tot[r["brand"]] += 1
        if r["discount_pct"]:
            g[r["brand"]].append(float(r["discount_pct"]))
    lines = []
    for b, v in sorted(g.items(), key=lambda kv: -st.median(kv[1])):
        if len(v) < MIN_N:
            continue
        share = len(v) / tot[b] * 100
        deep = sum(1 for x in v if x >= 30) / len(v) * 100
        lines.append(f"{b:<24}{len(v):>6}{share:>9.0f}%{st.median(v):>11.0f}%{deep:>11.0f}%")
    table("DISCOUNT DEPTH (list price vs selling price)",
          f"{'brand':<24}{'n':>6}{'on promo':>10}{'median':>11}{'>=30% off':>12}", lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default="data/catalog.csv")
    args = ap.parse_args()
    rows = load(args.catalog)
    print(f"loaded {len(rows)} rows "
          f"({sum(1 for r in rows if r['form'] in SEATING)} upholstered seating)")
    coverage(rows)
    positioning(rows)
    by_form(rows)
    discounting(rows)
