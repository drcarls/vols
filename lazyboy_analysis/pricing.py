"""Pricing: where the line sits, what it discounts to, and what it buys.

Every retailer here shows both a list price and a selling price, on essentially
every SKU, so each brand can be read twice -- where it positions itself and
where it actually transacts. Those two answers differ, and the difference is
the finding.

Four passes:
  1. list versus street position, indexed to the focus brand
  2. discount depth and, separately, its dispersion
  3. price per named feature -- what the money buys
  4. the focus brand's own price ladder, and where it leaves gaps
"""

import csv
import argparse
import statistics as st
from collections import defaultdict

from assortment import load, load_descriptions

CATS = ("Recliners", "Motion sofas")


def med(v):
    return st.median(v) if v else None


def section_position(rows, focus, minn):
    """List price says where a brand aims; street price says where it lands."""
    print("=" * 100)
    print("1. LIST POSITION vs STREET POSITION".center(100))
    print("=" * 100)
    for ret in ("slumberland", "steinhafels"):
        for cat in CATS:
            sub = [r for r in rows if r["retailer"] == ret and r["cat"] == cat
                   and r["list_price"]]
            if not sub:
                continue
            by = defaultdict(list)
            for r in sub:
                by[r["brand"]].append(r)
            base = by.get(focus)
            if not base or len(base) < minn:
                continue
            b_list = med([float(x["list_price"]) for x in base])
            b_street = med([x["price"] for x in base])

            print(f"\n-- {ret} · {cat}  ({focus} = 100) --")
            print(f"{'brand':<24}{'n':>5}{'list':>9}{'street':>9}"
                  f"{'list idx':>10}{'street idx':>12}{'shift':>8}")
            print("-" * 77)
            rank = sorted((b for b, v in by.items() if len(v) >= minn),
                          key=lambda b: -med([float(x["list_price"]) for x in by[b]]))
            for b in rank:
                v = by[b]
                li = med([float(x["list_price"]) for x in v])
                stt = med([x["price"] for x in v])
                li_i, st_i = li / b_list * 100, stt / b_street * 100
                mark = "  <<" if b == focus else ""
                print(f"{b:<24}{len(v):>5}{li:>9,.0f}{stt:>9,.0f}"
                      f"{li_i:>10.0f}{st_i:>12.0f}{st_i - li_i:>+8.0f}{mark}")
    print("\n  shift = street index minus list index. Negative means the brand")
    print("  discounts harder than the focus brand and lands lower than it lists.")


def section_discount(rows, focus, minn):
    """Depth is half the story; a brand can discount deeply and still be consistent."""
    print("\n\n" + "=" * 100)
    print("2. DISCOUNT DEPTH AND CONSISTENCY".center(100))
    print("=" * 100)
    for cat in CATS:
        by = defaultdict(list)
        for r in rows:
            if r["cat"] == cat and r["discount_pct"]:
                by[r["brand"]].append(float(r["discount_pct"]))
        print(f"\n-- {cat} --")
        print(f"{'brand':<24}{'n':>5}{'median':>9}{'p10':>7}{'p90':>7}"
              f"{'spread':>9}{'>=40% off':>11}")
        print("-" * 72)
        for b, v in sorted(by.items(), key=lambda kv: -med(kv[1])):
            if len(v) < minn:
                continue
            s = sorted(v)
            q = lambda p: s[min(int(len(s) * p), len(s) - 1)]
            deep = sum(1 for x in v if x >= 40) / len(v) * 100
            mark = "  <<" if b == focus else ""
            print(f"{b:<24}{len(v):>5}{med(v):>8.0f}%{q(.10):>6.0f}%{q(.90):>6.0f}%"
                  f"{q(.90) - q(.10):>8.0f}pt{deep:>10.0f}%{mark}")
    print("\n  spread = p90 minus p10, in percentage points. A wide spread means")
    print("  two shoppers buying the same brand get very different deals.")


def section_value(rows, focus, minn):
    """What a dollar buys, using the features a listing actually advertises."""
    print("\n\n" + "=" * 100)
    print("3. WHAT THE PRICE BUYS".center(100))
    print("=" * 100)
    for cat in CATS:
        by = defaultdict(list)
        for r in rows:
            if r["cat"] == cat:
                by[r["brand"]].append(r)
        print(f"\n-- {cat} --")
        print(f"{'brand':<24}{'n':>5}{'street $':>10}{'feats':>7}"
              f"{'$ per feature':>15}{'% power':>9}{'% headrest':>12}")
        print("-" * 82)
        ranked = []
        for b, v in by.items():
            if len(v) < minn:
                continue
            f = st.mean([x["feats"] for x in v])
            if f <= 0:
                continue
            ranked.append((b, v, med([x["price"] for x in v]) / f, f))
        for b, v, per, f in sorted(ranked, key=lambda t: t[2]):
            pw = sum(1 for x in v if "power" in x["product"].lower()) / len(v) * 100
            hr = sum(1 for x in v if "headrest" in x["product"].lower()) / len(v) * 100
            mark = "  <<" if b == focus else ""
            print(f"{b:<24}{len(v):>5}{med([x['price'] for x in v]):>10,.0f}"
                  f"{f:>7.1f}{per:>15,.0f}{pw:>8.0f}%{hr:>11.0f}%{mark}")
    print("\n  Lower $ per feature is more advertised capability per dollar. It")
    print("  measures what listings claim, not a teardown, so it rewards brands")
    print("  that describe their products fully.")


def section_ladder(rows, focus):
    """Where the focus brand's own price ladder is dense and where it thins out."""
    print("\n\n" + "=" * 100)
    print(f"4. {focus.upper()}'S OWN PRICE LADDER".center(100))
    print("=" * 100)
    for ret in ("slumberland", "steinhafels"):
        for cat in CATS:
            v = sorted(r["price"] for r in rows
                       if r["retailer"] == ret and r["cat"] == cat and r["brand"] == focus)
            if len(v) < 8:
                continue
            others = sorted(r["price"] for r in rows
                            if r["retailer"] == ret and r["cat"] == cat
                            and r["brand"] != focus)
            print(f"\n-- {ret} · {cat}  ({len(v)} {focus} SKUs, "
                  f"${v[0]:,.0f}–${v[-1]:,.0f}) --")
            bands = [(0, 750), (750, 1250), (1250, 1750), (1750, 2500),
                     (2500, 3500), (3500, 10 ** 9)]
            print(f"   {'band':<18}{focus:>10}{'competitors':>14}{'':>4}")
            for lo, hi in bands:
                mine = sum(1 for p in v if lo <= p < hi)
                theirs = sum(1 for p in others if lo <= p < hi)
                if not mine and not theirs:
                    continue
                label = f"${lo:,}–{hi:,}" if hi < 10 ** 9 else f"${lo:,}+"
                bar = "#" * min(mine, 30)
                gap = "  <- no cover" if theirs >= 8 and mine == 0 else ""
                print(f"   {label:<18}{mine:>10}{theirs:>14}   {bar}{gap}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--skus", default="data/skus.csv")
    ap.add_argument("--brand", default="La-Z-Boy")
    ap.add_argument("--min-n", type=int, default=8)
    a = ap.parse_args()
    rows = load(a.skus, load_descriptions())
    section_position(rows, a.brand, a.min_n)
    section_discount(rows, a.brand, a.min_n)
    section_value(rows, a.brand, a.min_n)
    section_ladder(rows, a.brand)
