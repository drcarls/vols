"""Where La-Z-Boy SKUs sit in each retailer's price ladder.

A retailer that carries La-Z-Boy alongside competing brands decides, per
category, which brand a shopper meets first and which they are shown next. A
La-Z-Boy SKU priced below a dense cluster of competitor SKUs is functioning as
the opening price point for that cluster: the shopper anchors on it, then steps
up into someone else's product.

What is measurable here is the ladder structure, not the retailer's intent.
"Tees up N competitor SKUs" means N competitor SKUs sit within one step above
this SKU in the same store and category -- it does not prove the retailer
planned it that way.
"""

import csv
import re
import argparse
import statistics as st
from collections import defaultdict, Counter

SEATING = {"Recliner", "Sofa", "Loveseat", "Sectional"}
FOCUS = "La-Z-Boy"

# Spare parts and add-ons carry a seating category but are not furniture, and
# at $40-$150 they would otherwise look like the cheapest seat in the store.
# Matched on the title rather than a price floor, so that a genuinely cheap
# recliner (Ashley's Nerviano, $270) survives.
ACCESSORY_RE = re.compile(
    r"^\s*(arc |tall |wall )*(handle|base)s?\s*$|sheet set|sleep kit|"
    r"sofa table|swatch|topper|protector|\bpad\b|cup holder", re.I)


def pct_rank(value, population):
    if not population:
        return None
    below = sum(1 for p in population if p < value)
    return round(below / len(population) * 100, 1)


def analyse(rows, window):
    """Per focus-brand SKU: its rank in the local ladder and what sits just above."""
    peers = defaultdict(list)          # (retailer, form) -> competitor prices
    peer_rows = defaultdict(list)
    for r in rows:
        if r["form"] not in SEATING:
            continue
        if r["brand"] != FOCUS:
            peers[(r["retailer"], r["form"])].append(r["price"])
            peer_rows[(r["retailer"], r["form"])].append(r)

    out = []
    for r in rows:
        if r["brand"] != FOCUS or r["form"] not in SEATING:
            continue
        key = (r["retailer"], r["form"])
        pop = peers[key]
        price = r["price"]
        ceiling = price * (1 + window / 100)
        above = [x for x in peer_rows[key] if price < x["price"] <= ceiling]
        # Count distinct competitor models, not colourways: six covers of one
        # sofa is one alternative on the floor, not six.
        models = {(x["brand"], x["product_id"]) for x in above}
        brands = Counter(b for b, _ in models)

        rank = pct_rank(price, pop)
        if rank is None:
            role = "No competitor set"
        elif rank <= 25:
            role = "Opening price point"
        elif rank >= 75:
            role = "Premium anchor"
        else:
            role = "Mid-ladder"

        out.append({
            **r,
            "peer_n": len(pop),
            "price_pctile": rank,
            "role": role,
            "tees_up_n": len(models),
            "tees_up_brands": "; ".join(f"{b}({n})" for b, n in brands.most_common()),
            "_models": models,
            "cheaper_competitors": sum(1 for x in pop if x < price),
        })
    return out


def main(path, window):
    rows, dropped = [], 0
    for r in csv.DictReader(open(path)):
        if ACCESSORY_RE.search(r["product"]):
            dropped += 1
            continue
        r["price"] = float(r["price"])
        rows.append(r)
    if dropped:
        print(f"(excluded {dropped} parts/accessory SKUs)\n")

    # ---- assortment across retailers -------------------------------------
    prods = defaultdict(set)
    skus = Counter()
    for r in rows:
        prods[(r["retailer"], r["brand"])].add(r["product_id"])
        skus[(r["retailer"], r["brand"])] += 1
    brands = sorted({r["brand"] for r in rows},
                    key=lambda b: -sum(skus[(x, b)] for x in ("slumberland", "steinhafels")))

    print("=== ASSORTMENT: SKUs carried by retailer ===\n")
    print(f"{'brand':<24}{'Slumberland':>22}{'Steinhafels':>22}")
    print(f"{'':<24}{'SKUs':>10}{'models':>12}{'SKUs':>10}{'models':>12}")
    print("-" * 68)
    for b in brands:
        s, t = skus[("slumberland", b)], skus[("steinhafels", b)]
        sp, tp = len(prods[("slumberland", b)]), len(prods[("steinhafels", b)])
        print(f"{b:<24}{s:>10}{sp:>12}{t:>10}{tp:>12}")
    tot_s = sum(skus[("slumberland", b)] for b in brands)
    tot_t = sum(skus[("steinhafels", b)] for b in brands)
    print("-" * 68)
    print(f"{'TOTAL':<24}{tot_s:>10}{'':>12}{tot_t:>10}{'':>12}")
    print(f"\nLa-Z-Boy share of tracked SKUs: "
          f"Slumberland {skus[('slumberland', FOCUS)] / tot_s * 100:.0f}%, "
          f"Steinhafels {skus[('steinhafels', FOCUS)] / tot_t * 100:.0f}%")

    # ---- lineup differences ----------------------------------------------
    print("\n\n=== LINEUP DIFFERENCES ===\n")
    only_s = [b for b in brands if skus[("slumberland", b)] and not skus[("steinhafels", b)]]
    only_t = [b for b in brands if skus[("steinhafels", b)] and not skus[("slumberland", b)]]
    print(f"  Slumberland only : {', '.join(only_s) or '-'}")
    print(f"  Steinhafels only : {', '.join(only_t) or '-'}")
    print(f"  Both             : {', '.join(b for b in brands if skus[('slumberland', b)] and skus[('steinhafels', b)])}")

    print(f"\n  La-Z-Boy form mix (SKUs):")
    print(f"  {'form':<12}{'Slumberland':>13}{'Steinhafels':>13}")
    fm = defaultdict(Counter)
    for r in rows:
        if r["brand"] == FOCUS and r["form"] in SEATING:
            fm[r["form"]][r["retailer"]] += 1
    for f in sorted(fm, key=lambda f: -sum(fm[f].values())):
        print(f"  {f:<12}{fm[f]['slumberland']:>13}{fm[f]['steinhafels']:>13}")

    # ---- ladder role ------------------------------------------------------
    res = analyse(rows, window)
    print(f"\n\n=== HOW LA-Z-BOY SKUs SIT IN THE LADDER (step-up window +{window}%) ===\n")
    print(f"{'retailer':<14}{'role':<22}{'SKUs':>6}{'median $':>11}{'competitor SKUs teed up':>26}")
    print("-" * 79)
    for ret in ("slumberland", "steinhafels"):
        sub = [r for r in res if r["retailer"] == ret]
        for role in ("Opening price point", "Mid-ladder", "Premium anchor"):
            g = [r for r in sub if r["role"] == role]
            if not g:
                continue
            print(f"{ret:<14}{role:<22}{len(g):>6}"
                  f"{st.median([r['price'] for r in g]):>11,.0f}"
                  f"{sum(r['tees_up_n'] for r in g):>26}")
        print(f"{'':<14}{'-- all --':<22}{len(sub):>6}"
              f"{st.median([r['price'] for r in sub]):>11,.0f}"
              f"{sum(r['tees_up_n'] for r in sub):>26}")

    # ---- the entry points -------------------------------------------------
    # A high step-up count on its own only means the SKU sits where competitor
    # prices are dense. It reads as teeing up competitors when the SKU is also
    # near the bottom of its ladder -- cheap enough to be the shopper's first
    # stop, with competitor product stacked just above it.
    print(f"\n\n=== ENTRY-POINT SKUs: bottom-quartile La-Z-Boy, competitors stacked above ===\n")
    entry = sorted([r for r in res if r["role"] == "Opening price point"],
                   key=lambda r: -r["tees_up_n"])
    print(f"{'retailer':<13}{'model':<30}{'form':<11}{'price':>8}{'disc':>6}"
          f"{'pct':>5}{'up':>4}  {'brands in the step-up window'}")
    print("-" * 116)
    seen = set()
    for r in entry:
        k = (r["retailer"], r["product"], r["form"])
        if k in seen:
            continue
        seen.add(k)
        disc = f"{float(r['discount_pct']):.0f}%" if r["discount_pct"] else "-"
        print(f"{r['retailer']:<13}{r['product'][:29]:<30}{r['form']:<11}"
              f"{r['price']:>8,.0f}{disc:>6}{r['price_pctile']:>5.0f}"
              f"{r['tees_up_n']:>4}  {r['tees_up_brands'][:46]}")
    if not entry:
        print("  (none)")

    print(f"\n  For contrast, the highest raw step-up counts sit mid-ladder --")
    print(f"  crowded price zones rather than entry points:")
    mid = sorted([r for r in res if r["role"] != "Opening price point"],
                 key=lambda r: -r["tees_up_n"])[:3]
    for r in mid:
        print(f"    {r['product'][:34]:<36}{r['form']:<11}${r['price']:>7,.0f}"
              f"  pctile {r['price_pctile']:>4.0f}  {r['tees_up_n']} models above")

    # ---- who benefits -----------------------------------------------------
    # Count distinct (La-Z-Boy model, competitor model) pairs. Counting SKU
    # rows on either side would just multiply by the number of colourways.
    pairs = defaultdict(set)
    for r in res:
        for b, pid in r["_models"]:
            pairs[b].add((r["retailer"], r["product"], b, pid))
    print(f"\n\n=== WHICH BRANDS SIT ONE STEP ABOVE A LA-Z-BOY MODEL ===\n")
    print(f"{'brand':<24}{'model pairs within +' + str(int(window)) + '%':>26}")
    print("-" * 50)
    for b, v in sorted(pairs.items(), key=lambda kv: -len(kv[1])):
        print(f"{b:<24}{len(v):>26}")

    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--skus", default="data/skus.csv")
    ap.add_argument("--window", type=float, default=30.0,
                    help="how far above a SKU still counts as one step up (%%)")
    ap.add_argument("--out", default="data/teeup_by_sku.csv")
    args = ap.parse_args()
    res = main(args.skus, args.window)
    cols = ["retailer", "brand", "sku", "product", "variant", "form", "material",
            "price", "list_price", "discount_pct", "available", "peer_n",
            "price_pctile", "role", "tees_up_n", "tees_up_brands",
            "cheaper_competitors"]
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(res, key=lambda r: -r["tees_up_n"]))
    print(f"\n\nper-SKU detail -> {args.out} ({len(res)} La-Z-Boy SKUs)")
