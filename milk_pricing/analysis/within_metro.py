"""The within-metro test: compare high-Black and low-Black Walmart stores that
share a metropolitan market, so no between-region confound is possible.

Backs reports/within_metro_test.md. Run from the milk_pricing/ package root.

Metro definitions below are conventional MSA approximations built from county
names in the price file, not official CBSA delineations.
"""
import csv
import math
import random
import statistics
from collections import defaultdict

import numpy as np

ATLANTA = {"Fulton", "DeKalb", "Gwinnett", "Cobb", "Clayton", "Cherokee", "Douglas", "Henry",
           "Fayette", "Rockdale", "Newton", "Paulding", "Coweta", "Forsyth", "Barrow", "Walton",
           "Carroll", "Spalding", "Bartow", "Hall"}
METROS = {
    "Atlanta": ("GA", ATLANTA),
    "Chicago": ("IL", {"Cook", "DuPage", "Lake", "Will", "Kane", "McHenry", "Kendall"}),
    "Memphis": ("TN", {"Shelby", "Fayette", "Tipton"}),
    "Birmingham": ("AL", {"Jefferson", "Shelby", "St. Clair", "Blount", "Bibb", "Walker", "Chilton"}),
    "Charlotte": ("NC", {"Mecklenburg", "Union", "Cabarrus", "Gaston", "Iredell", "Lincoln", "Rowan"}),
    "Jacksonville": ("FL", {"Duval", "Clay", "St. Johns", "Nassau", "Baker"}),
    "Houston": ("TX", {"Harris", "Fort Bend", "Montgomery", "Brazoria", "Galveston", "Liberty",
                       "Waller", "Chambers"}),
    "Dallas-FW": ("TX", {"Dallas", "Tarrant", "Collin", "Denton", "Ellis", "Johnson", "Kaufman",
                         "Rockwall", "Parker"}),
    "Detroit": ("MI", {"Wayne", "Oakland", "Macomb", "Livingston", "St. Clair", "Lapeer"}),
    "Cleveland": ("OH", {"Cuyahoga", "Lake", "Lorain", "Medina", "Geauga", "Summit", "Portage"}),
    "Richmond": ("VA", {"Henrico", "Chesterfield", "Hanover", "Richmond City"}),
    "Baltimore": ("MD", {"Baltimore", "Baltimore City", "Anne Arundel", "Howard", "Harford", "Carroll"}),
    "New Orleans": ("LA", {"Orleans", "Jefferson", "St. Tammany", "St. Bernard", "St. Charles",
                           "Plaquemines"}),
    "Columbia SC": ("SC", {"Richland", "Lexington", "Kershaw", "Fairfield", "Calhoun"}),
    "Charleston SC": ("SC", {"Charleston", "Berkeley", "Dorchester"}),
}
HI, LO = 30.0, 10.0


def load():
    out = []
    for r in csv.DictReader(open("data/national_walmart_official.csv")):
        if not (r["state"] and r["whole_milk"] and r["county"] and r["pct_black"]
                and r["median_income"] and r["population"]):
            continue
        out.append({"st": r["state"], "cty": r["county"], "p": float(r["whole_milk"]),
                    "blk": float(r["pct_black"]), "inc": float(r["median_income"]),
                    "pop": float(r["population"]),
                    "cls": float(r["class_I_diff_cwt"]) if r["class_I_diff_cwt"] else None})
    return out


def ols(cols, y):
    X = np.column_stack([np.ones(len(y))] + cols)
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ b
    k = np.linalg.matrix_rank(X)
    se = np.sqrt(np.diag(np.linalg.pinv(X.T @ X)) * (res @ res / max(len(y) - k, 1)))
    return b, b / se


def pair_diffs(B, W):
    """Nearest-neighbour match with replacement on income and log(population)."""
    out = []
    for h in B:
        best, bd = None, None
        for c in W:
            d = (abs(c["inc"] - h["inc"]) / 10000.0) ** 2 + \
                (abs(math.log(c["pop"]) - math.log(h["pop"]))) ** 2
            if bd is None or d < bd:
                bd, best = d, c
        if best:
            out.append(h["p"] - best["p"])
    return out


def matched(U):
    B = [r for r in U if r["blk"] >= HI]
    W = [r for r in U if r["blk"] <= LO]
    if len(B) < 5 or len(W) < 3:
        return None
    d = pair_diffs(B, W)
    if len(d) < 5:
        return None
    m, sd = statistics.mean(d), statistics.stdev(d)
    return len(d), len(W), m, (m / (sd / math.sqrt(len(d))) if sd else 0.0), sd


def perm_p(U, t0, trials=5000, seed=83):
    rng = random.Random(seed)
    nB = sum(1 for r in U if r["blk"] >= HI)
    nW = sum(1 for r in U if r["blk"] <= LO)
    ge = n = 0
    for _ in range(trials):
        sh = U[:]
        rng.shuffle(sh)
        d = pair_diffs(sh[:nB], sh[nB:nB + nW])
        if len(d) < 5 or statistics.stdev(d) == 0:
            continue
        n += 1
        if statistics.mean(d) / (statistics.stdev(d) / math.sqrt(len(d))) >= t0:
            ge += 1
    return ge / max(1, n)


def main():
    S = load()
    print("=== Metro sample and continuous specification ===")
    print(f"  {'metro':<15}{'n':>4}{'%Blk med':>10}{'>=30%':>7}{'<=10%':>7}{'sd $':>8}{'%Black coef':>24}")
    cells = []
    for name, (st, ctys) in METROS.items():
        V = [s for s in S if s["st"] == st and s["cty"] in ctys]
        if len(V) < 15:
            print(f"  {name:<15}{len(V):>4}  -- too few stores")
            continue
        b = [x["blk"] for x in V]
        y = np.array([x["p"] for x in V])
        bb, tt = ols([np.array(b), np.array([x["inc"] for x in V]) / 1000,
                      np.log(np.array([x["pop"] for x in V]))], y)
        hi = sum(1 for x in b if x >= HI)
        lo = sum(1 for x in b if x <= LO)
        print(f"  {name:<15}{len(V):>4}{np.median(b):>10.1f}{hi:>7}{lo:>7}{np.std(y):>8.3f}"
              f"{f'{bb[1]:+.5f} (t {tt[1]:+.2f})':>24}")
        cells.append((name, V, hi, lo))

    P, lab = [], []
    for name, V, hi, lo in cells:
        if hi >= 4 and lo >= 4:
            P += V
            lab += [name] * len(V)
    names = sorted(set(lab))
    D = [np.array([1.0 if l == n else 0.0 for l in lab]) for n in names[1:]]
    bb, tt = ols([np.array([x["blk"] for x in P]), np.array([x["inc"] for x in P]) / 1000,
                  np.log(np.array([x["pop"] for x in P]))] + D, np.array([x["p"] for x in P]))
    print(f"\n  pooled, metro FE: n={len(P)} across {len(names)} metros -> "
          f"%Black = {bb[1]:+.5f} (t {tt[1]:+.2f})")

    print("\n=== The memo's matched-pair design, inside each metro ===")
    alld = []
    for name, V, hi, lo in cells:
        r = matched(V)
        if not r:
            continue
        n_, w_, m_, t_, _ = r
        alld += pair_diffs([x for x in V if x["blk"] >= HI], [x for x in V if x["blk"] <= LO])
        extra = ""
        if name == "Atlanta":
            extra = f"  perm p={perm_p(V, t_):.4f}"
        print(f"  {name:<15}{n_:>3} pairs   gap ${m_:+.3f}  t {t_:+.2f}{extra}")
    m = statistics.mean(alld)
    t = m / (statistics.stdev(alld) / math.sqrt(len(alld)))
    print(f"\n  ALL METROS POOLED: {len(alld)} within-metro pairs   gap ${m:+.4f}   t {t:+.2f}")

    print("\n=== Atlanta detail: power, dose-response, county ladder ===")
    A = [s for s in S if s["st"] == "GA" and s["cty"] in ATLANTA]
    d = pair_diffs([x for x in A if x["blk"] >= HI], [x for x in A if x["blk"] <= LO])
    sd = statistics.stdev(d)
    se = sd / math.sqrt(len(d))
    print(f"  {len(d)} pairs, sd ${sd:.3f}, SE ${se:.4f}")
    print(f"  95% CI on the gap: ${statistics.mean(d) - 1.96 * se:+.3f} to "
          f"${statistics.mean(d) + 1.96 * se:+.3f}")
    print(f"  MDE (80% power, one-sided 5%): ${2.49 * se:.3f}/gal")
    print(f"  Class I differentials present: {sorted({x['cls'] for x in A if x['cls'] is not None})}")
    srt = sorted(A, key=lambda x: x["blk"])
    print("  by %Black sextile:")
    for i in range(0, len(srt), 12):
        g = srt[i:i + 12]
        print(f"    %Black {np.mean([x['blk'] for x in g]):5.1f} -> ${np.mean([x['p'] for x in g]):.3f}"
              f"  (n={len(g)})")
    byc = defaultdict(list)
    for x in A:
        byc[x["cty"]].append(x)
    print("  by county:")
    for c, v in sorted(byc.items(), key=lambda z: np.mean([x["blk"] for x in z[1]])):
        if len(v) < 2:
            continue
        print(f"    {c:<12} n={len(v):>2}  %Black {np.mean([x['blk'] for x in v]):5.1f}  "
              f"${np.mean([x['p'] for x in v]):.3f}  inc ${np.mean([x['inc'] for x in v]) / 1000:.0f}k")


if __name__ == "__main__":
    main()
