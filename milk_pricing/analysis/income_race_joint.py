"""Price on income and race jointly, by state, on ZIPs carrying both retailers.

Backs reports/income_race_joint.md.

WHY. The descriptive table (reports/rural_price_by_state.csv) shows rural Black ZIPs
paying more at BOTH retailers in 7 of 9 states. Those same ZIPs are also $18,584 poorer
on average, and milk turns out to cost MORE in poorer rural areas, so income predicts
part of the racial gap rather than explaining it away. This separates the two.

DESIGN. 1,003 rural ZIPs carry both a Walmart and an Aldi price, on identical
demographics, so race and income enter once and the two retailers are two outcomes
measured over the same geography. Everything is estimated with state fixed effects and
standard errors clustered on state; the raw pooled version is shown alongside because
the difference between them is itself the finding elsewhere in this project.
"""
import json
import sys

import numpy as np

sys.path.insert(0, "src")
from milk_pricing import panel

SEP = "data/aldi_2026_09.jsonl"


def load():
    sep = {json.loads(l)["zip"].zfill(5): json.loads(l) for l in open(SEP)}
    rows = [r for r in panel.load() if not str(r["geo"]).lower().startswith("urb")]
    out = []
    for r in rows:
        v = sep.get(r["zip"])
        if v and v.get("whole") is not None:
            r["aldi"] = float(v["whole"])
            out.append(r)
    return out


def ols(y, X, cluster):
    X = np.column_stack([np.ones(len(y)), X])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ b
    xi = np.linalg.pinv(X.T @ X)
    meat = np.zeros((X.shape[1],) * 2)
    for c in np.unique(cluster):
        m = cluster == c
        xu = X[m].T @ r[m]
        meat += np.outer(xu, xu)
    g = len(np.unique(cluster))
    V = xi @ meat @ xi * (g / (g - 1))
    return b[1:], np.sqrt(np.diag(V))[1:]


def main():
    S = load()
    blk = np.array([r["blk"] for r in S])
    inc = np.array([r["inc"] for r in S]) / 10000.0     # per $10k
    pop = np.log(np.array([r["pop"] for r in S]).clip(1))
    st = np.array([r["st"] for r in S])
    ks = sorted(set(st))
    D = np.column_stack([(st == k).astype(float) for k in ks[1:]])
    print(f"{len(S)} rural ZIPs carrying both retailers, {len(ks)} states\n")

    print("=== 1. Race and income entered together ===")
    print("    %Black coefficient is per percentage point; income per $10,000.\n")
    for lab, key in (("Walmart", "p"), ("Aldi", "aldi")):
        y = np.array([r[key] for r in S])
        print(f"  {lab}")
        for spec, X in (("race alone", np.column_stack([blk])),
                        ("race + income", np.column_stack([blk, inc])),
                        ("race + income + log pop", np.column_stack([blk, inc, pop])),
                        ("+ state fixed effects", np.column_stack([blk, inc, pop, D]))):
            b, se = ols(y, X, st)
            inc_txt = (f"   income {b[1]:+.4f} (t {b[1]/se[1]:+5.2f})"
                       if len(b) > 1 else "")
            print(f"    {spec:<26} %Black {b[0]:+.5f} (t {b[0]/se[0]:+5.2f}){inc_txt}")
        print()

    print("=== 2. How much of the raw gap is income? ===")
    hi, lo = blk >= 30, blk <= 10
    dinc = inc[hi].mean() - inc[lo].mean()
    dblk = blk[hi].mean() - blk[lo].mean()
    print(f"  Black rural ZIPs are {dinc*10000:+,.0f} in income and "
          f"{dblk:+.1f} points in Black share vs non-Black rural ZIPs\n")
    print(f"  {'':<9}{'raw gap':>10}{'from income':>13}{'from race':>11}{'residual':>10}")
    for lab, key in (("Walmart", "p"), ("Aldi", "aldi")):
        y = np.array([r[key] for r in S])
        raw = y[hi].mean() - y[lo].mean()
        b, _ = ols(y, np.column_stack([blk, inc, pop, D]), st)
        print(f"  {lab:<9}{raw:>+10.3f}{b[1]*dinc:>+13.3f}{b[0]*dblk:>+11.3f}"
              f"{raw-b[1]*dinc-b[0]*dblk:>+10.3f}")
    print("  (state fixed effects absorb the rest; the decomposition is indicative,")
    print("   applying linear coefficients to a difference in means.)")

    print("\n=== 3. State by state, race controlling for income ===")
    print(f"  {'st':<5}{'n':>5}{'Walmart %Blk':>14}{'Aldi %Blk':>12}"
          f"{'income (WM)':>13}{'both same sign':>16}")
    agree = tot = 0
    for s in ks:
        m = st == s
        if m.sum() < 12 or np.ptp(blk[m]) < 10:
            continue
        X = np.column_stack([blk[m], inc[m]])
        bw, _ = ols(np.array([r["p"] for r in S])[m], X, np.arange(m.sum()) % 5)
        ba, _ = ols(np.array([r["aldi"] for r in S])[m], X, np.arange(m.sum()) % 5)
        same = (bw[0] > 0) == (ba[0] > 0)
        agree += same
        tot += 1
        print(f"  {s:<5}{m.sum():>5}{bw[0]:>+14.5f}{ba[0]:>+12.5f}{bw[1]:>+13.4f}"
              f"{('yes' if same else 'NO'):>16}")
    print(f"\n  race coefficients agree in sign at the two retailers in {agree}/{tot} states")


if __name__ == "__main__":
    main()
