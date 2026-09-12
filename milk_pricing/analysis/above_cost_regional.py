"""Where the above-freight markup lands: the departure-from-cost gradient by region.

Backs reports/above_cost_regional.md.

The national test in reports/usdss.md pools regions with OPPOSITE signs. USDA prices
the California metros far below the USDSS cost surface and the South and Northeast above
it, so a national regression of the departure on %Black averages a large negative block
against a large positive one and loses power. That is a specification problem, not a
finding. This script removes the between-region contrast and asks the question inside
regions, where it is actually meaningful.

The gradient tested here is invariant to the additive shift used to align the two
surfaces (a constant added to every county cancels out of a slope), so unlike the
LEVEL of the departure it does not depend on that normalisation choice at all.

    python3 analysis/above_cost_regional.py
"""
import importlib.util
import sys

import numpy as np

spec = importlib.util.spec_from_file_location("u", "analysis/usdss.py")
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)
GAL = u.GAL_PER_CWT

NORTHEAST = {"CT","ME","MA","NH","RI","VT","NJ","NY","PA"}
MIDWEST   = {"IL","IN","MI","OH","WI","IA","KS","MN","MO","NE","ND","SD"}
SOUTH     = {"DE","FL","GA","MD","NC","SC","VA","WV","DC","AL","KY","MS","TN",
             "AR","LA","OK","TX"}
WEST      = {"AZ","CO","ID","MT","NV","NM","UT","WY","CA","OR","WA"}
# the FMMO south-east proper: orders 5 (Appalachian), 6 (Florida), 7 (Southeast)
SOUTHEAST = {"AL","AR","FL","GA","KY","LA","MS","NC","SC","TN","VA","WV"}

def region(st):
    for nm, s in (("Northeast", NORTHEAST), ("Midwest", MIDWEST),
                  ("South", SOUTH), ("West", WEST)):
        if st in s:
            return nm
    return "other"


def wls(y, X, w, cluster):
    s = np.sqrt(w)
    Xs, Ys = X * s[:, None], y * s
    b, *_ = np.linalg.lstsq(Xs, Ys, rcond=None)
    r = Ys - Xs @ b
    xi = np.linalg.pinv(Xs.T @ Xs)
    g = len(np.unique(cluster))
    if g < 3:
        return b[1], float("nan"), g
    meat = np.zeros((X.shape[1],) * 2)
    for c in np.unique(cluster):
        m = cluster == c
        xu = Xs[m].T @ r[m]
        meat += np.outer(xu, xu)
    V = xi @ meat @ xi * (g / (g - 1))
    return b[1], b[1] / np.sqrt(np.diag(V))[1], g


def perm_slope(dev, pb, w, st, obs, draws=3000, seed=7):
    """Reassign whole states' %Black blocks among the states in this sample."""
    rng = np.random.default_rng(seed)
    states = list(np.unique(st))
    if len(states) < 4:
        return float("nan")
    idx = {c: np.where(st == c)[0] for c in states}
    hits = 0
    for _ in range(draws):
        pm = dict(zip(states, rng.permutation(states)))
        npb = np.empty_like(pb)
        for c in states:
            src, dst = idx[pm[c]], idx[c]
            npb[dst] = np.resize(pb[src], len(dst))
        b, _, _ = wls(dev, np.column_stack([np.ones(len(dev)), npb]), w, st)
        if abs(b) >= abs(obs):
            hits += 1
    return hits / draws


def main():
    rows, _, _ = u.load()
    for r in rows:
        r["reg"] = region(r["st"])
    for lab, key in (("Class I dual", "c1"), ("Class I minus Class III", "gu")):
        shift = u.wm(rows, "new", "tot") - u.wm(rows, key, "tot")
        for r in rows:
            r["dev_" + key] = r["new"] - (r[key] + shift)

    for lab, key in (("Class I dual", "c1"), ("give-up charge", "gu")):
        dk = "dev_" + key
        print(f"\n{'='*78}\n  ABOVE-FREIGHT DEPARTURE vs %BLACK  —  benchmark: {lab}\n{'='*78}")

        # ---- 1. the national result, and why it is the wrong specification
        print("\n1. National, and the same thing with the between-region contrast removed")
        A = [r for r in rows]
        y = np.array([r[dk] for r in A]); pb = np.array([r["pctblk"] for r in A])
        w = np.array([float(r["tot"]) for r in A]); st = np.array([r["st"] for r in A])
        reg = np.array([r["reg"] for r in A])
        b, t, g = wls(y, np.column_stack([np.ones(len(A)), pb]), w, st)
        print(f"   national, no controls        {b:+.5f}/cwt/pt  t {t:+5.2f}   "
              f"({100*b/GAL:+.3f}c/gal per pt)")
        regs = sorted(set(reg))
        RD = np.column_stack([(reg == rr).astype(float) for rr in regs[1:]])
        b2, t2, _ = wls(y, np.column_stack([np.ones(len(A)), pb, RD]), w, st)
        print(f"   + census-region fixed effects {b2:+.5f}/cwt/pt  t {t2:+5.2f}   "
              f"({100*b2/GAL:+.3f}c/gal per pt)   <- removes the CA-vs-South contrast")
        noca = [r for r in rows if r["st"] != "CA"]
        b3, t3, _ = wls(np.array([r[dk] for r in noca]),
                        np.column_stack([np.ones(len(noca)),
                                         np.array([r["pctblk"] for r in noca])]),
                        np.array([float(r["tot"]) for r in noca]),
                        np.array([r["st"] for r in noca]))
        print(f"   national, California dropped {b3:+.5f}/cwt/pt  t {t3:+5.2f}")

        # ---- 2. within each region
        print("\n2. Within each census region")
        print(f"   {'region':<12}{'counties':>9}{'states':>8}{'mean dev':>10}"
              f"{'coef':>11}{'t':>7}{'c/gal/pt':>10}{'perm p':>9}")
        for rr in regs:
            G = [r for r in rows if r["reg"] == rr]
            if len(G) < 30:
                continue
            yy = np.array([r[dk] for r in G]); pp = np.array([r["pctblk"] for r in G])
            ww = np.array([float(r["tot"]) for r in G]); ss = np.array([r["st"] for r in G])
            bb, tt, gg = wls(yy, np.column_stack([np.ones(len(G)), pp]), ww, ss)
            pv = perm_slope(yy, pp, ww, ss, bb)
            md = np.average(yy, weights=ww)
            print(f"   {rr:<12}{len(G):>9}{gg:>8}{md:>+10.3f}{bb:>+11.5f}{tt:>+7.2f}"
                  f"{100*bb/GAL:>+10.3f}{pv:>9.3f}")

        # ---- 3. the FMMO south-east proper
        print("\n3. The FMMO south-east proper (orders 5, 6, 7 — 12 states)")
        S = [r for r in rows if r["st"] in SOUTHEAST]
        yy = np.array([r[dk] for r in S]); pp = np.array([r["pctblk"] for r in S])
        ww = np.array([float(r["tot"]) for r in S]); ss = np.array([r["st"] for r in S])
        bb, tt, gg = wls(yy, np.column_stack([np.ones(len(S)), pp]), ww, ss)
        pv = perm_slope(yy, pp, ww, ss, bb)
        print(f"   {len(S)} counties, {gg} states, {sum(r['tot'] for r in S):,.0f} people")
        print(f"   mean departure from freight   {np.average(yy, weights=ww):+.3f}/cwt "
              f"({100*np.average(yy, weights=ww)/GAL:+.2f}c/gal)")
        print(f"   slope on %Black              {bb:+.5f}/cwt/pt  t {tt:+.2f}  "
              f"perm p {pv:.3f}   ({100*bb/GAL:+.3f}c/gal per pt)")
        # the incidence version: person-weighted Black vs White mean of the departure
        blk = sum(r[dk] * r["blk"] for r in S) / sum(r["blk"] for r in S)
        wht = sum(r[dk] * r["wht"] for r in S) / sum(r["wht"] for r in S)
        print(f"   Black-weighted {blk:+.3f} vs White-weighted {wht:+.3f}  "
              f"-> gap {100*(blk-wht)/GAL:+.2f}c/gal")
        # dose-response across %Black quintiles
        S2 = sorted(S, key=lambda r: r["pctblk"])
        qs = np.array_split(S2, 5)
        print(f"\n   dose-response across %Black quintiles, south-east only:")
        print(f"   {'quintile':<10}{'%Black':>9}{'adopted':>10}{'freight':>10}{'departure':>12}")
        for i, q in enumerate(qs, 1):
            wq = np.array([float(r["tot"]) for r in q])
            print(f"   Q{i:<9}{np.average([r['pctblk'] for r in q], weights=wq):>9.1f}"
                  f"{np.average([r['new'] for r in q], weights=wq):>10.2f}"
                  f"{np.average([r[key] for r in q], weights=wq) + (u.wm(rows,'new','tot')-u.wm(rows,key,'tot')):>10.2f}"
                  f"{np.average([r[dk] for r in q], weights=wq):>+12.3f}")


if __name__ == "__main__":
    main()
