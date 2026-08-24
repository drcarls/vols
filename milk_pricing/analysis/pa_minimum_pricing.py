"""Does Pennsylvania's minimum retail milk price fall disproportionately on Black households?

Backs reports/pa_minimum_pricing.md. Run from the milk_pricing/ package root.

The headline is the decomposition in section 4: nationally the milk BURDEN
(cost / income) rises steeply with %Black, while the milk PRICE falls. The
disparity is the income denominator, not the price numerator.
"""
import csv
from collections import Counter

import numpy as np

GAL_PER_YEAR = 104.0  # 2 gal/week; affects the level, not the signs or t-stats
PHILLY = {"Philadelphia", "Delaware", "Montgomery", "Bucks", "Chester"}
NEIGHBOURS = ("NJ", "NY", "OH", "MD", "WV", "DE")


def load():
    out = []
    for r in csv.DictReader(open("data/national_walmart_official.csv")):
        if not (r["whole_milk"] and r["state"] and r["county"] and r["pct_black"]
                and r["median_income"] and r["population"]):
            continue
        if float(r["median_income"]) <= 0:
            continue
        out.append({"st": r["state"], "cty": r["county"], "geo": r["geo"],
                    "p": float(r["whole_milk"]), "blk": float(r["pct_black"]),
                    "inc": float(r["median_income"]), "pop": float(r["population"])})
    return out


def ols(cols, y):
    X = np.column_stack([np.ones(len(y))] + cols)
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ b
    k = np.linalg.matrix_rank(X)
    se = np.sqrt(np.diag(np.linalg.pinv(X.T @ X)) * (res @ res / max(len(y) - k, 1)))
    return b, b / se


def main():
    S = load()
    PA = [s for s in S if s["st"] == "PA"]

    print(f"=== 1. Within PA: {len(PA)} stores, {len(set(s['p'] for s in PA))} regulated prices ===")
    print(f"  {'price':>7}{'stores':>8}{'%Black':>9}{'median inc':>12}{'urban':>8}")
    for p, n in sorted(Counter(s["p"] for s in PA).items()):
        g = [s for s in PA if s["p"] == p]
        print(f"  ${p:>6.2f}{n:>8}{np.mean([s['blk'] for s in g]):>9.1f}"
              f"{np.median([s['inc'] for s in g]):>12,.0f}"
              f"{100 * np.mean([s['geo'] == 'urban' for s in g]):>7.0f}%")
    y = np.array([s["p"] for s in PA])
    b, t = ols([np.array([s["blk"] for s in PA])], y)
    b2, t2 = ols([np.array([s["blk"] for s in PA]), np.array([s["inc"] for s in PA]) / 1000,
                  np.log(np.array([s["pop"] for s in PA])),
                  np.array([1.0 if s["geo"] == "urban" else 0.0 for s in PA])], y)
    print(f"\n  price on %Black: raw {b[1]:+.5f} (t {t[1]:+.2f})   "
          f"+controls {b2[1]:+.5f} (t {t2[1]:+.2f})")
    ph = [s for s in PA if s["cty"] in PHILLY]
    rest = [s for s in PA if s["cty"] not in PHILLY]
    print(f"  Philadelphia 5-county ${np.mean([s['p'] for s in ph]):.2f} "
          f"({np.mean([s['blk'] for s in ph]):.1f}% Black)   "
          f"rest of PA ${np.mean([s['p'] for s in rest]):.2f} "
          f"({np.mean([s['blk'] for s in rest]):.1f}% Black)")

    print("\n=== 2. Is PA's Black population even in the sample? ===")
    b_ = [s["blk"] for s in PA]
    print(f"  median %Black {np.median(b_):.1f}   p90 {np.percentile(b_, 90):.1f}   max {max(b_):.1f}")
    print(f"  ZIPs >=20% Black: {sum(1 for x in b_ if x >= 20)}   "
          f">=30%: {sum(1 for x in b_ if x >= 30)}   (PA is ~12% Black statewide)")

    print("\n=== 3. The size of the floor ===")
    for st in ("PA",) + NEIGHBOURS:
        g = [s for s in S if s["st"] == st]
        if len(g) < 10:
            continue
        print(f"  {st}: n={len(g):>3}  ${np.mean([s['p'] for s in g]):.2f}  "
              f"sd ${np.std([s['p'] for s in g]):.3f}  {len(set(s['p'] for s in g))} prices")
    nb = [s for s in S if s["st"] in NEIGHBOURS]
    gap = np.mean([s["p"] for s in PA]) - np.mean([s["p"] for s in nb])
    print(f"  PA premium: ${gap:+.2f}/gal  = ${gap * GAL_PER_YEAR:,.0f}/household/year")
    for lab, g in (("PA", PA), ("neighbours", nb)):
        print(f"    {lab:<12} burden {100 * np.mean([GAL_PER_YEAR * s['p'] / s['inc'] for s in g]):.3f}% of income")

    print("\n=== 4. National decomposition: burden vs price vs income ===")
    sts = sorted({s["st"] for s in S})
    D = [np.array([1.0 if s["st"] == k else 0.0 for s in S]) for k in sts[1:]]
    blk = np.array([s["blk"] for s in S])
    for lab, y_ in (("burden (pp of income)",
                     np.array([100 * GAL_PER_YEAR * s["p"] / s["inc"] for s in S])),
                    ("price ($/gal)", np.array([s["p"] for s in S])),
                    ("median income ($k)", np.array([s["inc"] for s in S]) / 1000)):
        b1, t1 = ols([blk], y_)
        b3, t3 = ols([blk] + D, y_)
        print(f"  {lab:<24} raw {b1[1]:+.5f} (t {t1[1]:+.2f})    "
              f"+state FE {b3[1]:+.5f} (t {t3[1]:+.2f})")
    print("\n  -> the affordability disparity is the income denominator; the price gradient is negative.")


if __name__ == "__main__":
    main()
