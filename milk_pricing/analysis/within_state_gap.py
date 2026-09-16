"""Is there a Black/white price gap WITHIN states, or only between them?

Backs reports/within_state_gap.md.

WHY. An earlier summary described the part of the raw rural gap not explained by
income as "which state you are in". That phrasing conflates two different claims:
(a) Black rural ZIPs sit disproportionately in states where everyone pays more, and
(b) within a given state, Black and white rural ZIPs pay the same. (a) can be true
while (b) is false, and this script tests (b) directly instead of inferring it from
the fact that state fixed effects absorb the residual.

DESIGN. Three passes over the same 1,003 rural ZIPs that carry both retailers:
  1. the pooled %Black slope with and without state fixed effects, income excluded,
     so the only question is whether the gradient survives demeaning by state;
  2. each state's own Black-minus-white difference in means, unadjusted;
  3. the same within-state comparison after income enters, which is where the
     within-state gradient is expected to weaken.
Standard errors cluster on state in the pooled models. The per-state rows are
descriptive; with 20-200 ZIPs per state they carry real sampling noise and are
reported with their own n and a paired sign test across states rather than
individually starred.
"""
import json
import sys

import numpy as np

sys.path.insert(0, "src")
from milk_pricing import panel

SEP = "data/aldi_2026_09.jsonl"
HI, LO = 30.0, 10.0          # %Black thresholds for the descriptive contrast


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
    inc = np.array([r["inc"] for r in S]) / 10000.0
    st = np.array([r["st"] for r in S])
    ks = sorted(set(st))
    D = np.column_stack([(st == k).astype(float) for k in ks[1:]])
    W = np.array([r["p"] for r in S])
    A = np.array([r["aldi"] for r in S])
    print(f"{len(S)} rural ZIPs carrying both retailers, {len(ks)} states\n")

    print("=== 1. Does the %Black gradient survive demeaning by state? ===")
    print("    Income is deliberately NOT in these models. The only difference")
    print("    between the two rows is whether comparisons are made across states")
    print("    or inside them.\n")
    print(f"  {'':<26}{'Walmart':>22}{'Aldi':>22}")
    for spec, X in (("pooled across states", np.column_stack([blk])),
                    ("within state (state FE)", np.column_stack([blk, D]))):
        bw, sw = ols(W, X, st)
        ba, sa = ols(A, X, st)
        print(f"  {spec:<26}{bw[0]:>+12.5f} (t {bw[0]/sw[0]:+5.2f})"
              f"{ba[0]:>+12.5f} (t {ba[0]/sa[0]:+5.2f})")
    print("\n    Coefficient is dollars per gallon per percentage point of Black share.")
    print(f"    A {HI:.0f}-point swing in Black share moves the within-state Walmart")
    bw, sw = ols(W, np.column_stack([blk, D]), st)
    ba, sa = ols(A, np.column_stack([blk, D]), st)
    print(f"    price {bw[0]*HI:+.3f} and Aldi {ba[0]*HI:+.3f} per gallon.")

    print(f"\n=== 2. Each state's own Black-minus-white gap, unadjusted ===")
    print(f"    >={HI:.0f}% Black rural ZIPs vs <={LO:.0f}% Black rural ZIPs, same state.\n")
    print(f"  {'st':<4}{'n hi':>6}{'n lo':>6}{'WM hi':>9}{'WM lo':>9}{'WM gap':>9}"
          f"{'AL hi':>9}{'AL lo':>9}{'AL gap':>9}{'income gap':>12}")
    wg, ag, rows = [], [], []
    for s in ks:
        hi = (st == s) & (blk >= HI)
        lo = (st == s) & (blk <= LO)
        if hi.sum() < 5 or lo.sum() < 5:
            continue
        gw = W[hi].mean() - W[lo].mean()
        ga = A[hi].mean() - A[lo].mean()
        di = (inc[hi].mean() - inc[lo].mean()) * 10000
        wg.append(gw)
        ag.append(ga)
        rows.append((s, hi.sum(), lo.sum(), gw, ga, di))
        print(f"  {s:<4}{hi.sum():>6}{lo.sum():>6}{W[hi].mean():>9.3f}{W[lo].mean():>9.3f}"
              f"{gw:>+9.3f}{A[hi].mean():>9.3f}{A[lo].mean():>9.3f}{ga:>+9.3f}"
              f"{di:>+12,.0f}")
    wg, ag = np.array(wg), np.array(ag)
    print(f"\n  states with a positive Walmart gap: {(wg > 0).sum()}/{len(wg)}"
          f"   mean {wg.mean():+.3f}   median {np.median(wg):+.3f}")
    print(f"  states with a positive Aldi gap:    {(ag > 0).sum()}/{len(ag)}"
          f"   mean {ag.mean():+.3f}   median {np.median(ag):+.3f}")
    print(f"  both retailers positive in the same state: "
          f"{((wg > 0) & (ag > 0)).sum()}/{len(wg)}")

    print("\n=== 3. The same within-state contrast, after income ===")
    print("    Race and income together, state fixed effects, clustered on state.\n")
    print(f"  {'':<26}{'Walmart':>22}{'Aldi':>22}")
    X = np.column_stack([blk, inc, D])
    bw, sw = ols(W, X, st)
    ba, sa = ols(A, X, st)
    print(f"  {'%Black':<26}{bw[0]:>+12.5f} (t {bw[0]/sw[0]:+5.2f})"
          f"{ba[0]:>+12.5f} (t {ba[0]/sa[0]:+5.2f})")
    print(f"  {'income per $10k':<26}{bw[1]:>+12.5f} (t {bw[1]/sw[1]:+5.2f})"
          f"{ba[1]:>+12.5f} (t {ba[1]/sa[1]:+5.2f})")

    print("\n=== 4. Where the raw within-state gap goes ===")
    print("    Applying the model above to each state's own hi-vs-lo differences.\n")
    print(f"  {'st':<4}{'WM raw gap':>12}{'from income':>13}{'from race':>11}{'left over':>11}")
    for s, nh, nl, gw, ga, di in rows:
        print(f"  {s:<4}{gw:>+12.3f}{bw[1]*di/10000:>+13.3f}"
              f"{bw[0]*(blk[(st==s)&(blk>=HI)].mean()-blk[(st==s)&(blk<=LO)].mean()):>+11.3f}"
              f"{gw - bw[1]*di/10000 - bw[0]*(blk[(st==s)&(blk>=HI)].mean()-blk[(st==s)&(blk<=LO)].mean()):>+11.3f}")




def addendum():
    """Section 5, appended after the fact: split the headline gap into the part
    that is a comparison inside a state and the part that is a comparison between
    states, without leaning on a linear extrapolation."""
    S = load()
    blk = np.array([r["blk"] for r in S])
    st = np.array([r["st"] for r in S])
    W = np.array([r["p"] for r in S])
    A = np.array([r["aldi"] for r in S])
    print("\n=== 5. How much of the headline gap is a within-state comparison? ===")
    print("    Raw gap uses every ZIP. Within-state gap subtracts each state's own")
    print("    mean price first, so only ZIPs compared to their own state count.\n")
    for lo_t, hi_t, lab in ((10.0, 50.0, ">=50% Black vs <=10% Black"),
                            (10.0, 30.0, ">=30% Black vs <=10% Black")):
        print(f"  {lab}")
        print(f"    {'':<10}{'raw gap':>10}{'within-state':>14}{'between-state':>15}"
              f"{'% within':>10}")
        for nm, y in (("Walmart", W), ("Aldi", A)):
            hi, lo = blk >= hi_t, blk <= lo_t
            raw = y[hi].mean() - y[lo].mean()
            dm = y.copy()
            for s in set(st):
                m = st == s
                dm[m] = y[m] - y[m].mean()
            # only states holding both groups can support a within comparison
            ok = np.zeros(len(y), bool)
            for s in set(st):
                m = st == s
                if (m & hi).sum() and (m & lo).sum():
                    ok |= m
            wi = dm[hi & ok].mean() - dm[lo & ok].mean()
            print(f"    {nm:<10}{raw:>+10.3f}{wi:>+14.3f}{raw-wi:>+15.3f}"
                  f"{100*wi/raw if raw else float('nan'):>9.0f}%")
        print()


if __name__ == "__main__":
    main()
    addendum()
