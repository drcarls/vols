"""Why South Carolina has large within-state Walmart milk price variation.

Rules out a collection artifact, the Class I differential, and a zone boundary;
shows the spread is a metro discount; and decomposes SC's raw racial gap.

Backs reports/why_sc_varies.md. Run from the milk_pricing/ package root.
"""
import csv
import json
import numpy as np
from collections import Counter, defaultdict

NAMES = {"290": "Columbia", "291": "Columbia", "292": "Columbia", "293": "Rock Hill",
         "294": "Charleston", "295": "Florence", "296": "Greenville",
         "297": "Spartanburg", "298": "Aiken", "299": "Beaufort/Savannah"}


def national():
    return [r for r in csv.DictReader(open("data/national_walmart_official.csv"))
            if r["whole_milk"] and r["state"]]


def sc_rows(R):
    return [{"zip": r["zip"].zfill(5), "z3": r["zip"].zfill(5)[:3], "cty": r["county"],
             "p": float(r["whole_milk"]),
             "two": float(r["milk_2pct"]) if r["milk_2pct"] else None,
             "blk": float(r["pct_black"] or 0), "inc": float(r["median_income"] or 0),
             "pop": float(r["population"] or 0), "geo": r["geo"]}
            for r in R if r["state"] == "SC"]


def ols(cols, y):
    X = np.column_stack([np.ones(len(y))] + cols)
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ b
    k = np.linalg.matrix_rank(X)
    se = np.sqrt(np.diag(np.linalg.pinv(X.T @ X)) * (res @ res / max(len(y) - k, 1)))
    return b, b / se


def section_not_artifact(R, SC):
    print("=== 1. Not a collection artifact ===")
    a = {r["zip"].zfill(5): float(r["whole_milk"]) for r in R if r["state"] == "SC"}
    b = {r["zip"].zfill(5): float(r["whole_milk"])
         for r in csv.DictReader(open("data/sc_walmart_official.csv")) if r["whole_milk"]}
    both = set(a) & set(b)
    print(f"  ZIPs in both SC collections: {len(both)}  "
          f"max |difference| ${max(abs(a[z] - b[z]) for z in both):.2f}")
    for lab, f in (("LOW  (<$3.00)", lambda s: s["p"] < 3.0),
                   ("HIGH (>=$3.00)", lambda s: s["p"] >= 3.0)):
        G = [s for s in SC if f(s) and s["two"] is not None]
        same = np.mean([abs(s["p"] - s["two"]) < 0.005 for s in G])
        print(f"  {lab:<16} n={len(G):>3}  whole and 2% identical in {100 * same:.0f}% of stores")
    nat = [r for r in R if r["milk_2pct"]]
    big = np.mean([abs(float(r["whole_milk"]) - float(r["milk_2pct"])) > 0.5 for r in nat])
    print(f"  nationally, stores with a whole-vs-2% gap over $0.50: {100 * big:.1f}%")
    P = sorted(s["p"] for s in SC)
    lo = [p for p in P if p < 3.0]
    print(f"  SC distribution: n={len(P)} sd ${np.std(P):.3f} IQR ${np.percentile(P, 75) - np.percentile(P, 25):.2f}"
          f"  |  {len(lo)} stores ${min(lo):.2f}-${max(lo):.2f}, "
          f"{len(P) - len(lo)} stores ${min(p for p in P if p >= 3):.2f}-${max(P):.2f}")


def section_not_classI(R):
    print("\n=== 2. Not the Class I differential ===")
    for st in ("SC", "NC", "MS", "LA", "VA", "CA"):
        v = [float(r["class_I_diff_cwt"]) for r in R if r["state"] == st and r["class_I_diff_cwt"]]
        p = [float(r["whole_milk"]) for r in R if r["state"] == st]
        print(f"  {st}: Class I ${np.mean(v):.2f}/cwt   mean shelf ${np.mean(p):.2f}   sd ${np.std(p):.3f}")


def section_not_zone(R, SC):
    print("\n=== 3. Not a zone boundary: is the low band clean inside regions? ===")
    byz = defaultdict(list)
    for s in SC:
        byz[s["z3"]].append(s)
    for z, v in sorted(byz.items()):
        lo = sum(1 for x in v if x["p"] < 3.0)
        print(f"  {z} {NAMES.get(z, '?'):<18} {lo:>2}/{len(v):<2} below $3.00   "
              f"mean ${np.mean([x['p'] for x in v]):.2f}")
    print("\n  same check in the other bimodal states:")
    for st in ("NC", "TX", "OH", "IL", "AZ"):
        g = defaultdict(list)
        for r in R:
            if r["state"] == st:
                g[r["zip"].zfill(5)[:3]].append(float(r["whole_milk"]))
        multi = [v for v in g.values() if len(v) > 1]
        pure = sum(1 for v in multi if all(x < 3 for x in v) or all(x >= 3 for x in v))
        print(f"    {st}: {pure}/{len(multi)} ({100 * pure / len(multi):.0f}%) of multi-store "
              f"ZIP3 regions sit entirely on one side of $3.00")


def section_metro(SC):
    print("\n=== 4. It is the metro discount ===")
    y = np.array([1.0 if s["p"] < 3.0 else 0.0 for s in SC])
    inc = np.array([s["inc"] for s in SC]) / 1000
    blk = np.array([s["blk"] for s in SC])
    urb = np.array([1.0 if s["geo"] == "urban" else 0.0 for s in SC])
    inland = np.array([1.0 if s["z3"] in ("290", "291", "292", "296", "297", "298") else 0.0
                       for s in SC])
    for lab, cols, names in (("income only", [inc], ["income"]),
                             ("%Black only", [blk], ["%Black"]),
                             ("inland only", [inland], ["inland"]),
                             ("urban only", [urb], ["urban"]),
                             ("all four", [inc, urb, blk, inland],
                              ["income", "urban", "%Black", "inland"])):
        b, t = ols(cols, y)
        print(f"  P(low band) ~ {lab:<14} " +
              "  ".join(f"{names[i]}={b[i + 1]:+.4f}(t{t[i + 1]:+.2f})" for i in range(len(names))))


def section_cross_state(R):
    print("\n=== 5. Dispersion IS the urban-rural gap ===")
    A = json.load(open("data/aldi_pooled.json"))
    real = {z for z, v in A.items() if v.get("whole") and abs(v["whole"] - 2.19) > 0.005}
    bys = defaultdict(list)
    for r in R:
        bys[r["state"]].append({"zip": r["zip"].zfill(5), "p": float(r["whole_milk"]), "geo": r["geo"]})
    print(f"  {'st':<4}{'stores':>7}{'price sd':>10}{'urban-rural':>13}{'Aldi cover':>12}")
    rows = []
    for st, V in sorted(bys.items()):
        if len(V) < 50:
            continue
        swept = [s for s in V if s["zip"] in A]
        if len(swept) < 8:
            continue
        u = [s["p"] for s in V if s["geo"] == "urban"]
        rr = [s["p"] for s in V if s["geo"] == "rural"]
        if not (u and rr):
            continue
        cov = sum(1 for s in swept if s["zip"] in real) / len(swept)
        rows.append((st, len(V), np.std([s["p"] for s in V]), np.mean(u) - np.mean(rr), cov))
    for st, n, sd, gap, cov in sorted(rows, key=lambda z: -z[2]):
        print(f"  {st:<4}{n:>7}{sd:>10.3f}{gap:>+13.3f}{100 * cov:>11.0f}%")
    sd = np.array([r[2] for r in rows])
    gap = np.array([r[3] for r in rows])
    cov = np.array([r[4] for r in rows])
    print(f"\n  corr(price sd, Aldi coverage)      = {np.corrcoef(sd, cov)[0, 1]:+.3f}  (n={len(rows)})")
    print(f"  corr(urban-rural gap, Aldi coverage) = {np.corrcoef(gap, cov)[0, 1]:+.3f}")
    print("  NOTE: Aldi coverage here is Instacart delivery reach, not store proximity. Suggestive only.")


def section_racial_gap(SC):
    print("\n=== 6. SC's raw racial gap is composition ===")
    for geo in ("urban", "rural"):
        G = [s for s in SC if s["geo"] == geo]
        print(f"  {geo:<6} n={len(G):>2}  mean ${np.mean([s['p'] for s in G]):.2f}  "
              f"mean %Black {np.mean([s['blk'] for s in G]):.1f}")
    hi = [s for s in SC if s["blk"] >= 30]
    lo = [s for s in SC if s["blk"] <= 10]
    for lab, G in ((">=30% Black", hi), ("<=10% Black", lo)):
        print(f"  {lab:<12} n={len(G):>2}  mean ${np.mean([s['p'] for s in G]):.2f}  "
              f"urban share {100 * np.mean([s['geo'] == 'urban' for s in G]):.0f}%")
    print(f"  raw gap ${np.mean([s['p'] for s in hi]) - np.mean([s['p'] for s in lo]):+.3f}")
    for geo in ("urban", "rural"):
        h = [s["p"] for s in hi if s["geo"] == geo]
        l = [s["p"] for s in lo if s["geo"] == geo]
        print(f"    within {geo:<6}: high-Black ${np.mean(h):.2f} (n={len(h)}) vs "
              f"low-Black ${np.mean(l):.2f} (n={len(l)})  gap ${np.mean(h) - np.mean(l):+.3f}")


if __name__ == "__main__":
    R = national()
    SC = sc_rows(R)
    section_not_artifact(R, SC)
    section_not_classI(R)
    section_not_zone(R, SC)
    section_metro(SC)
    section_cross_state(R)
    section_racial_gap(SC)
