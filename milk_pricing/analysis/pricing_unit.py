"""Recover the geographic unit at which Walmart sets its milk price.

Backs reports/walmart_pricing_geography.md sections 3 and 4.
Run from the milk_pricing/ package root:  python3 analysis/pricing_unit.py
Input: data/national_walmart_official.csv (4,149 stores, one price each).
"""
import csv
import numpy as np
from collections import Counter, defaultdict

GAL_PER_CWT = 11.6289


def load():
    out = []
    for r in csv.DictReader(open("data/national_walmart_official.csv")):
        if not (r["store_id"] and r["whole_milk"] and r["state"] and r["county"] and r["zip"]):
            continue
        out.append({
            "store": r["store_id"], "st": r["state"], "cty": r["county"],
            "zip": r["zip"].zfill(5), "z3": r["zip"].zfill(5)[:3], "z2": r["zip"].zfill(5)[:2],
            "geo": r["geo"], "p": float(r["whole_milk"]),
            "cls": float(r["class_I_diff_cwt"]) if r["class_I_diff_cwt"] else None,
            "blk": float(r["pct_black"]) if r["pct_black"] else None,
            "inc": float(r["median_income"]) if r["median_income"] else None,
            "pop": float(r["population"]) if r["population"] else None,
        })
    return out


def r2(rows, y, key):
    """Share of variance in y explained by the partition `key`."""
    g = defaultdict(list)
    for s, v in zip(rows, y):
        g[key(s)].append(v)
    gm = {k: np.mean(v) for k, v in g.items()}
    wss = sum(sum((np.array(v) - gm[k]) ** 2) for k, v in g.items())
    return 1 - wss / sum((y - y.mean()) ** 2), len(g)


def nested(rows, y, coarse, fine):
    """Share of the coarse partition's residual variance that the fine partition explains."""
    g = defaultdict(list)
    for s, v in zip(rows, y):
        g[coarse(s)].append(v)
    gm = {k: np.mean(v) for k, v in g.items()}
    res = np.array([v - gm[coarse(s)] for s, v in zip(rows, y)])
    g2 = defaultdict(list)
    for s, v in zip(rows, res):
        g2[fine(s)].append(v)
    m2 = {k: np.mean(v) for k, v in g2.items()}
    wss = sum(sum((np.array(v) - m2[k]) ** 2) for k, v in g2.items())
    return 1 - wss / max(sum(res ** 2), 1e-12)


def ols(rows, cols, y, gkey=None, clkey=None, of_interest=1):
    """OLS with optional fixed effects and cluster-robust SEs. Returns (beta, t, n_clusters)."""
    n = len(rows)
    X = np.column_stack([np.ones(n)] + cols)
    if gkey:
        gs = sorted({gkey(s) for s in rows})
        if len(gs) > 1:
            X = np.column_stack([X] + [np.array([1.0 if gkey(s) == g else 0.0 for s in rows])
                                       for g in gs[1:]])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ b
    k = np.linalg.matrix_rank(X)
    XtXi = np.linalg.pinv(X.T @ X)
    if clkey:
        cl = sorted({clkey(s) for s in rows})
        meat = np.zeros((X.shape[1],) * 2)
        for c in cl:
            idx = [i for i, s in enumerate(rows) if clkey(s) == c]
            v = X[idx].T @ res[idx]
            meat += np.outer(v, v)
        G = len(cl)
        scale = (G / (G - 1)) * ((n - 1) / max(n - k, 1)) if G > 1 else 1
        se = np.sqrt(np.diag(XtXi @ meat @ XtXi * scale))
        return b[of_interest], b[of_interest] / se[of_interest], G
    se = np.sqrt(np.diag(XtXi) * (res @ res / max(n - k, 1)))
    return b[of_interest], b[of_interest] / se[of_interest], None


def section_price_grid(S):
    print("=== The price grid ===")
    c = Counter(s["p"] for s in S)
    print(f"  {len(S)} stores, {len({s['store'] for s in S})} distinct store ids, "
          f"{len(c)} distinct prices")
    top5 = sum(n for _, n in c.most_common(5))
    print(f"  top-5 price points cover {100 * top5 / len(S):.1f}% of stores")


def section_zone_blocks(S):
    print("\n=== Zone pricing: largest single-price blocks by state ===")
    bys = defaultdict(list)
    for s in S:
        bys[s["st"]].append(s)
    print(f"  {'st':<4}{'stores':>7}{'prices':>8}{'largest block':>15}{'counties spanned':>18}{'share':>8}")
    for st, v in sorted(bys.items()):
        if len(v) < 20:
            continue
        c = Counter(x["p"] for x in v)
        mp, mc = c.most_common(1)[0]
        ctys = len({x["cty"] for x in v if x["p"] == mp})
        print(f"  {st:<4}{len(v):>7}{len(c):>8}{mc:>15}{ctys:>18}{100 * mc / len(v):>7.1f}%")


def section_partition(S):
    print("\n=== Which partition is the pricing unit? (national, ln price) ===")
    y = np.log(np.array([s["p"] for s in S]))
    n = len(S)
    print(f"  {'partition':<26}{'groups':>8}{'R^2':>9}{'adj R^2':>10}")
    parts = [("ZIP2 prefix", lambda s: s["z2"]), ("state", lambda s: s["st"]),
             ("ZIP3 region", lambda s: s["z3"]), ("state x ZIP3", lambda s: (s["st"], s["z3"])),
             ("county", lambda s: (s["st"], s["cty"]))]
    for lbl, key in parts:
        a, ng = r2(S, y, key)
        adj = 1 - (1 - a) * (n - 1) / max(n - ng, 1)
        print(f"  {lbl:<26}{ng:>8}{100 * a:>8.1f}%{100 * adj:>9.1f}%")
    print("\n  nested (does the finer unit add anything?):")
    for lbl, co, fi in (("county on top of state x ZIP3", lambda s: (s["st"], s["z3"]), lambda s: (s["st"], s["cty"])),
                        ("ZIP3 on top of county", lambda s: (s["st"], s["cty"]), lambda s: (s["st"], s["z3"]))):
        print(f"    {lbl:<34}{100 * nested(S, y, co, fi):>6.1f}% of residual")
    print("\n  price uniformity within a unit:")
    for lbl, key in (("county", lambda s: (s["st"], s["cty"])), ("ZIP3 region", lambda s: (s["st"], s["z3"]))):
        g = defaultdict(list)
        for s in S:
            g[key(s)].append(s["p"])
        multi = {k: v for k, v in g.items() if len(v) > 1}
        same = sum(1 for v in multi.values() if len(set(v)) == 1)
        d = [max(v) - min(v) for v in multi.values()]
        print(f"    {lbl:<14} {len(multi)} multi-store units, {100 * same / len(multi):.1f}% uniform, "
              f"range median ${np.median(d):.2f} p90 ${np.percentile(d, 90):.2f}")
    byc = defaultdict(set)
    cnt = Counter((s["st"], s["cty"]) for s in S)
    for s in S:
        byc[(s["st"], s["cty"])].add(s["p"])
    multi = {k: v for k, v in byc.items() if cnt[k] > 1}
    split = sum(1 for v in multi.values() if len(v) > 1)
    print(f"    multi-store counties split across >=2 price blocks: {split}/{len(multi)} "
          f"({100 * split / len(multi):.0f}%)")


def section_classI(S):
    print("\n=== Class I differential pass-through ===")
    C = [s for s in S if s["cls"] is not None]
    y = np.array([s["p"] for s in C])
    cls = np.array([s["cls"] for s in C])
    b, t, _ = ols(C, [cls], y)
    print(f"  no FE     : {b:+.4f} $/gal per $1/cwt (t {t:+.2f})  -> pass-through {b * GAL_PER_CWT:.2f}x")
    b, t, _ = ols(C, [cls], y, gkey=lambda s: s["st"])
    print(f"  state FE  : {b:+.4f} (t {t:+.2f})  -> pass-through {b * GAL_PER_CWT:.2f}x")
    ly = np.log(y)
    a, ng = r2(C, ly, lambda s: s["cls"])
    print(f"  Class I zone alone explains {100 * a:.1f}% of ln-price variance ({ng} zones); "
          f"within state it adds {100 * nested(C, ly, lambda s: s['st'], lambda s: (s['st'], s['cls'])):.1f}% "
          f"of the residual")


def section_finding_b(S):
    print("\n=== Finding B under three definitions of the pricing region ===")
    print("    rural Walmart price on %Black, controlling income + log(pop)")
    R = [s for s in S if s["geo"] == "rural" and s["blk"] is not None
         and s["inc"] is not None and s["pop"]]
    print(f"  {'st':<4}{'n':>4}{'no FE':>20}{'ZIP3-region FE':>22}{'county FE':>20}{'Class I zone FE':>22}")
    for st in ("SC", "LA", "MS", "AR", "NC", "AL", "GA", "TN", "TX"):
        V = [s for s in R if s["st"] == st]
        if len(V) < 25:
            continue
        y = np.array([s["p"] for s in V])
        cols = [np.array([s["blk"] for s in V]),
                np.array([s["inc"] for s in V]) / 1000,
                np.log(np.array([s["pop"] for s in V]))]
        cells = []
        for gk in (None, lambda s: s["z3"], lambda s: (s["st"], s["cty"]), lambda s: s["cls"]):
            b, t, _ = ols(V, cols, y, gkey=gk)
            cells.append(f"{b:+.5f} (t {t:+.2f})")
        print(f"  {st:<4}{len(V):>4}{cells[0]:>20}{cells[1]:>22}{cells[2]:>20}{cells[3]:>22}")

    print("\n  SC and LA: region FE, SE clustered on region, within-region permutation on %Black")
    for st in ("LA", "SC"):
        V = [s for s in R if s["st"] == st]
        y = np.array([s["p"] for s in V])
        inc = np.array([s["inc"] for s in V]) / 1000
        lp = np.log(np.array([s["pop"] for s in V]))
        base = np.array([s["blk"] for s in V])
        b, t, G = ols(V, [base, inc, lp], y, gkey=lambda s: s["z3"], clkey=lambda s: s["z3"])
        rng = np.random.default_rng(19)
        z3s = sorted({s["z3"] for s in V})
        idxby = {g: [i for i, s in enumerate(V) if s["z3"] == g] for g in z3s}
        null = []
        for _ in range(3000):
            v = base.copy()
            for g in z3s:
                v[idxby[g]] = rng.permutation(v[idxby[g]])
            null.append(ols(V, [v, inc, lp], y, gkey=lambda s: s["z3"])[0])
        null = np.array(null)
        print(f"    {st}: n={len(V)} regions={G}  %Black={b:+.5f} (cluster t {t:+.2f})  "
              f"permutation one-sided p={np.mean(null >= b):.4f} two-sided p={np.mean(np.abs(null) >= abs(b)):.4f}")

    print("\n  do the racial tails coexist within a ZIP3 region?")
    for st in ("SC", "LA"):
        V = [s for s in R if s["st"] == st]
        hi = [s for s in V if s["blk"] >= 30]
        lo = [s for s in V if s["blk"] <= 10]
        zh, zl = {s["z3"] for s in hi}, {s["z3"] for s in lo}
        ph, pl = {s["p"] for s in hi}, {s["p"] for s in lo}
        print(f"    {st}: {len(hi)} high-Black / {len(lo)} low-Black stores; "
              f"ZIP3 regions shared {len(zh & zl)}/{len(zl)} of the low-Black regions; "
              f"price points shared {len(ph & pl)}/{len(pl)}; "
              f"raw gap ${np.mean([s['p'] for s in hi]) - np.mean([s['p'] for s in lo]):+.3f}")


if __name__ == "__main__":
    S = load()
    section_price_grid(S)
    section_zone_blocks(S)
    section_partition(S)
    section_classI(S)
    section_finding_b(S)
