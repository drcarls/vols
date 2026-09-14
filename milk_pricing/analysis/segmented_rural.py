"""The client's own design: segment Black/white within income and urbanicity.

Backs reports/segmented_rural.md. Written after the client pushed back on a summary
that described the retail finding as uniformly null. They were right to push.

    python3 analysis/segmented_rural.py

WHY THIS EXISTS. The within-metro tests that carried `reports/within_metro_test.md`
(Atlanta, then twelve metros) are URBAN BY CONSTRUCTION. The client's design is a
stratified comparison inside income x urbanicity cells, and the cell where their
result lives is BOTTOM-INCOME-QUARTILE RURAL - a segment the metro tests cannot
reach. Pooling the two hides it, because the urban cells run the other way and
cancel the rural ones out.

WHAT IT SHOWS. Their finding reproduces. It is also not robust: the sign depends on
how "same area" is defined, and it does not survive clustering.
"""
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, "src")
from milk_pricing import panel


def D(k):
    ks = sorted(set(k))
    return (np.column_stack([(k == x).astype(float) for x in ks[1:]])
            if len(ks) > 1 else np.empty((len(k), 0)))


def ols(y, X, cluster=None):
    X = np.column_stack([np.ones(len(y)), X])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ b
    xi = np.linalg.pinv(X.T @ X)
    if cluster is None:
        V = xi * (r @ r / max(len(y) - X.shape[1], 1))
    else:
        meat = np.zeros((X.shape[1],) * 2)
        for c in np.unique(cluster):
            m = cluster == c
            xu = X[m].T @ r[m]
            meat += np.outer(xu, xu)
        g = len(np.unique(cluster))
        if g < 3:
            return b[1], float("nan")
        V = xi @ meat @ xi * (g / (g - 1))
    se = np.sqrt(np.diag(V))
    return b[1], b[1] / se[1]


def main():
    rows = panel.load()
    p = np.array([float(r["p"]) for r in rows])
    blk = np.array([float(r["blk"]) for r in rows])
    inc = np.array([float(r["inc"]) for r in rows])
    pop = np.log(np.array([float(r["pop"]) for r in rows]).clip(1))
    urb = np.array([1.0 if str(r["geo"]).lower().startswith("urb") else 0.0 for r in rows])
    st = np.array([r["st"] for r in rows])
    cty = np.array([r["cty"] for r in rows])
    z3 = np.array([r["z3"] for r in rows])
    iq = np.digitize(inc, np.quantile(inc, [.25, .5, .75]))

    print(f"clean panel n={len(rows)}, {len(set(st))} states\n")

    print("=== 1. Pooled: the specification that looks null ===")
    for lab, X in (("%Black + income + urbanicity", np.column_stack([blk, inc, urb])),
                   ("  + log population", np.column_stack([blk, inc, urb, pop]))):
        b, t0 = ols(p, X)
        _, t1 = ols(p, X, cluster=st)
        print(f"  {lab:<34}{b:>+12.5f}  t {t0:+.2f} (naive)  t {t1:+.2f} (clustered)")

    print("\n=== 2. The same thing, split by cell — the pooling is what hides it ===")
    print(f"  {'cell':<24}{'n hi':>6}{'n lo':>6}{'hi-Black':>10}{'low-Black':>11}{'gap':>9}")
    for q in range(4):
        for u in (0, 1):
            m = (iq == q) & (urb == u)
            hi, lo = m & (blk >= 30), m & (blk <= 10)
            if hi.sum() < 5 or lo.sum() < 5:
                continue
            print(f"  Q{q+1} income, {'urban' if u else 'rural':<6}{'':<7}{hi.sum():>6}{lo.sum():>6}"
                  f"{p[hi].mean():>10.3f}{p[lo].mean():>11.3f}{p[hi].mean()-p[lo].mean():>+9.3f}")
    print("  Rural cells run positive, urban cells negative. Pooled they cancel.")

    m = (iq == 0) & (urb == 0)
    print(f"\n=== 3. Bottom-quartile-income RURAL, n={m.sum()} — where the finding lives ===")
    base = np.column_stack([blk[m], inc[m], pop[m]])
    print(f"  {'geographic control':<30}{'coef $/gal per pt':>19}{'t naive':>10}{'t clust':>10}")
    for lab, X in (("none", base),
                   ("state fixed effects", np.column_stack([base, D(st[m])])),
                   ("ZIP3 fixed effects", np.column_stack([base, D(z3[m])])),
                   ("county fixed effects", np.column_stack([base, D(cty[m])]))):
        b, t0 = ols(p[m], X)
        _, t1 = ols(p[m], X, cluster=st[m])
        print(f"  {lab:<30}{b:>+19.5f}{t0:>+10.2f}{t1:>+10.2f}")
    print("  THE SIGN DEPENDS ON THE CONTROL. That instability is the finding.")

    hi, lo = m & (blk >= 30), m & (blk <= 10)
    print("\n=== 4. Why: the two groups are in different places ===")
    print("  high-Black:", Counter(st[hi]).most_common(7))
    print("  low-Black :", Counter(st[lo]).most_common(7))
    ch, cl = set(cty[hi]), set(cty[lo])
    print(f"  counties with high-Black {len(ch)}, low-Black {len(cl)}, BOTH {len(ch & cl)}")

    print("\n=== 5. Same-state comparison inside the cell ===")
    print(f"  {'state':<7}{'n hi':>6}{'n lo':>6}{'hi $':>9}{'lo $':>9}{'gap':>9}")
    tot = []
    for s in sorted(set(st[hi]) & set(st[lo])):
        a, b_ = hi & (st == s), lo & (st == s)
        if a.sum() < 3 or b_.sum() < 3:
            continue
        g = p[a].mean() - p[b_].mean()
        tot.append((g, a.sum() + b_.sum()))
        print(f"  {s:<7}{a.sum():>6}{b_.sum():>6}{p[a].mean():>9.3f}{p[b_].mean():>9.3f}{g:>+9.3f}")
    w = np.array([x[1] for x in tot]); gv = np.array([x[0] for x in tot])
    print(f"\n  weighted within-state gap {np.average(gv, weights=w):+.4f}/gal, "
          f"positive in {(gv > 0).sum()} of {len(gv)} states")
    print(f"  against {p[hi].mean()-p[lo].mean():+.4f} pooled across states")


if __name__ == "__main__":
    main()
