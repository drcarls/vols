"""Assortment structure in the two categories where La-Z-Boy actually competes.

Three questions, in order: how much of each retailer's shelf each brand holds,
how those SKUs differ in features and materials, and where La-Z-Boy's own SKUs
sit in the resulting ladder.

Material note. La-Z-Boy names leather in the model title and does not name
fabric. Steinhafels corroborates this independently: its variant codes carry an
LB prefix on leather and D/E/C on fabric, and across 47 La-Z-Boy models the two
never cross. So "leather" here means explicitly identified as leather, and the
share is a floor -- unnamed leather would be missed, never invented.
"""

import csv
import json
import re
import argparse
import statistics as st
from collections import defaultdict, Counter

from teeup import ACCESSORY_RE

# Ordered so the richest feature named in a title wins the description.
FEATURES = {
    "power": r"\bpower\b|\bp[23]\b|powerrecline",
    "headrest": r"head\s?rest",
    "lumbar": r"lumbar",
    "zero-gravity": r"zero\s?grav",
    "massage": r"massage",
    "heat": r"\bheat(ed|ing)?\b",
    "lift": r"\blift\b",
    "swivel": r"swivel|glider|rocker",
    "usb": r"\busb\b|charging",
    "storage": r"storage|console|cup\s?holder",
}
LEATHER_RE = re.compile(r"leather", re.I)
LB_CODE_RE = re.compile(r"^\s*LB\d", re.I)


def category(r):
    if r["form"] == "Recliner":
        return "Recliners"
    if r["form"] in ("Sofa", "Loveseat") and r["motion"] == "Motion":
        return "Motion sofas"
    return None


def material_of(r):
    if LB_CODE_RE.match(r["variant"] or ""):
        return "Leather"
    return "Leather" if LEATHER_RE.search(r["product"] or "") else "Fabric"


def load_descriptions(data_dir="data"):
    """Product descriptions, keyed by product id."""
    out = {}
    for name in ("slumberland", "steinhafels"):
        for p in json.load(open(f"{data_dir}/{name}_products.json")):
            out[str(p["id"])] = re.sub(r"<[^>]+>", " ", p.get("body_html") or "")
    return out


def feature_count(r, descriptions):
    """Features named anywhere the shopper would see them.

    Counting titles alone favours brands with terse naming: reading the
    descriptions too moves Flexsteel from 8th to 2nd on recliners. This measures
    what a listing advertises, not a teardown -- a tersely listed product is
    indistinguishable here from a genuinely plain one.
    """
    text = f"{r['product']} {r['variant']} {descriptions.get(r['product_id'], '')}"
    return sum(1 for pat in FEATURES.values() if re.search(pat, text, re.I))


def load(path, descriptions):
    rows = []
    for r in csv.DictReader(open(path)):
        if ACCESSORY_RE.search(r["product"]):
            continue
        cat = category(r)
        if not cat:
            continue
        r["price"] = float(r["price"])
        r["cat"] = cat
        r["mat"] = material_of(r)
        r["feats"] = feature_count(r, descriptions)
        rows.append(r)
    return rows


def pctile(value, pop):
    return sum(1 for p in pop if p < value) / len(pop) * 100 if pop else None


def role_of(pct):
    if pct <= 10:
        return "Opening price point"
    if pct <= 30:
        return "Value"
    if pct <= 70:
        return "Mid tier"
    if pct <= 90:
        return "Upper mid"
    return "Premium"


def section_counts(rows, focus, minn):
    print("=" * 96)
    print("1. WHAT EACH RETAILER CARRIES".center(96))
    print("=" * 96)
    for ret in ("slumberland", "steinhafels"):
        for cat in ("Recliners", "Motion sofas"):
            sub = [r for r in rows if r["retailer"] == ret and r["cat"] == cat]
            if not sub:
                continue
            by = defaultdict(list)
            for r in sub:
                by[r["brand"]].append(r)
            total = len(sub)
            print(f"\n-- {ret} · {cat} — {total} SKUs across {len(by)} brands --")
            print(f"{'brand':<24}{'SKUs':>6}{'share':>8}{'models':>8}{'median $':>11}"
                  f"{'feats':>7}{'leather':>9}")
            print("-" * 73)
            for b, v in sorted(by.items(), key=lambda kv: -len(kv[1])):
                if len(v) < minn and b != focus:
                    continue
                lea = sum(1 for x in v if x["mat"] == "Leather") / len(v) * 100
                mark = "  <<" if b == focus else ""
                print(f"{b:<24}{len(v):>6}{len(v)/total*100:>7.0f}%"
                      f"{len({x['product_id'] for x in v}):>8}"
                      f"{st.median([x['price'] for x in v]):>11,.0f}"
                      f"{st.mean([x['feats'] for x in v]):>7.1f}"
                      f"{lea:>8.0f}%{mark}")


def section_differences(rows, focus, minn):
    print("\n\n" + "=" * 96)
    print("2. HOW THE SKUs DIFFER".center(96))
    print("=" * 96)
    print("\n  feats = mean count of named features out of 10 (power, headrest,")
    print("  lumbar, zero-gravity, massage, heat, lift, swivel, usb, storage),")
    print("  read from the title and the product description together.\n")
    for cat in ("Recliners", "Motion sofas"):
        sub = [r for r in rows if r["cat"] == cat]
        by = defaultdict(list)
        for r in sub:
            by[r["brand"]].append(r)
        print(f"\n-- {cat} (both retailers) --")
        print(f"{'brand':<24}{'SKUs':>6}{'median $':>11}{'feats':>7}"
              f"{'% power':>9}{'% headrest':>12}{'% leather':>11}")
        print("-" * 80)
        ordered = sorted((b for b, v in by.items() if len(v) >= minn),
                         key=lambda b: -st.mean([x["feats"] for x in by[b]]))
        for b in ordered:
            v = by[b]
            pw = sum(1 for x in v if re.search(FEATURES["power"], f"{x['product']}", re.I))
            hr = sum(1 for x in v if re.search(FEATURES["headrest"], f"{x['product']}", re.I))
            lea = sum(1 for x in v if x["mat"] == "Leather")
            mark = "  <<" if b == focus else ""
            print(f"{b:<24}{len(v):>6}{st.median([x['price'] for x in v]):>11,.0f}"
                  f"{st.mean([x['feats'] for x in v]):>7.1f}{pw/len(v)*100:>8.0f}%"
                  f"{hr/len(v)*100:>11.0f}%{lea/len(v)*100:>10.0f}%{mark}")


def section_roles(rows, focus, window):
    print("\n\n" + "=" * 96)
    print(f"3. HOW {focus.upper()} SKUs ARE USED".center(96))
    print("=" * 96)
    for ret in ("slumberland", "steinhafels"):
        for cat in ("Recliners", "Motion sofas"):
            peers = [r for r in rows if r["retailer"] == ret and r["cat"] == cat
                     and r["brand"] != focus]
            mine = [r for r in rows if r["retailer"] == ret and r["cat"] == cat
                    and r["brand"] == focus]
            if not mine or not peers:
                continue
            pop = [r["price"] for r in peers]
            print(f"\n-- {ret} · {cat} — {len(mine)} {focus} SKUs vs {len(pop)} competitor SKUs --")
            print(f"{'role':<22}{'material':<10}{'SKUs':>6}{'median $':>11}"
                  f"{'feats':>7}{'cheaper below':>15}{'within +' + str(int(window)) + '%':>13}")
            print("-" * 84)
            buckets = defaultdict(list)
            for r in mine:
                pct = pctile(r["price"], pop)
                buckets[(role_of(pct), r["mat"])].append((r, pct))
            order = ["Opening price point", "Value", "Mid tier", "Upper mid", "Premium"]
            for role in order:
                for mat in ("Fabric", "Leather"):
                    g = buckets.get((role, mat))
                    if not g:
                        continue
                    below = st.median([sum(1 for p in pop if p < r["price"]) for r, _ in g])
                    above = st.median([
                        len({(x["brand"], x["product_id"]) for x in peers
                             if r["price"] < x["price"] <= r["price"] * (1 + window / 100)})
                        for r, _ in g])
                    print(f"{role:<22}{mat:<10}{len(g):>6}"
                          f"{st.median([r['price'] for r, _ in g]):>11,.0f}"
                          f"{st.mean([r['feats'] for r, _ in g]):>7.1f}"
                          f"{below:>15.0f}{above:>13.0f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--skus", default="data/skus.csv")
    ap.add_argument("--brand", default="La-Z-Boy")
    ap.add_argument("--min-n", type=int, default=8)
    ap.add_argument("--window", type=float, default=30.0)
    a = ap.parse_args()
    rows = load(a.skus, load_descriptions())
    section_counts(rows, a.brand, a.min_n)
    section_differences(rows, a.brand, a.min_n)
    section_roles(rows, a.brand, a.window)
