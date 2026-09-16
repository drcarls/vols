"""Milk price by racial composition, holding income equal.

Backs reports/income_adjusted.md.

WHY. Rural Black ZIPs pay 27-32 cents/gal more at Walmart than rural white ZIPs,
and they are also ~$18,600 poorer, in a market where poorer rural areas pay more.
The question this answers is the counterfactual one: if Black and white rural ZIPs
had the same income, what would the price difference be?

DESIGN. Four ways of equalising income, because the answer should not depend on
the functional form:
  1. linear   - price residualised on median income, group means of the residual
                shifted back onto the grand mean, so the numbers read as prices;
  2. decile   - each ZIP compared only to ZIPs in its own national income decile,
                the ten within-decile gaps pooled by decile size; no functional
                form at all;
  3. matched  - each high-Black ZIP paired with the nearest low-Black ZIP on
                income within a $2,000 caliper, unmatched ZIPs dropped;
  4. +state   - the linear adjustment with state fixed effects, which additionally
                holds constant which state the ZIP is in.
Methods 1-3 equalise income only. Method 4 is reported because between-state
composition is the larger part of the raw gap (reports/within_state_gap.md).

Standard errors cluster on state throughout; with 11-30 state clusters they are
wide, and the point estimates carry the argument, not the stars.
"""
import json
import sys

import numpy as np

sys.path.insert(0, "src")
from milk_pricing import panel

SEP = "data/aldi_2026_09.jsonl"
CALIPER = 2000.0


def rural(both=False):
    rows = [r for r in panel.load() if not str(r["geo"]).lower().startswith("urb")]
    if not both:
        return rows
    sep = {json.loads(l)["zip"].zfill(5): json.loads(l) for l in open(SEP)}
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
    return b, np.sqrt(np.diag(V))


def groups(blk):
    """The three contrasts used throughout this project."""
    return [(">=50% Black", blk >= 50), ("30-50% Black", (blk >= 30) & (blk < 50)),
            ("10-30% Black", (blk >= 10) & (blk < 30)), ("<=10% Black", blk <= 10)]


# The contrasts run through every method. "majority" is the definition the cover
# memo leads with; the 30/10 pair is the wider-net version kept for continuity.
CONTRASTS = [
    ("majority Black vs majority white", lambda b, w: (b >= 50, w >= 50)),
    (">=30% Black vs <=10% Black", lambda b, w: (b >= 30, b <= 10)),
]


def adjusted_levels(y, inc, st, blk, fe=False):
    """Group mean prices after removing the income gradient.

    Residualise on income (and optionally state), then add the sample mean price
    back so the output is on the price scale rather than centred on zero. This is
    the price each group would pay if every ZIP sat at the sample-average income.
    """
    X = np.column_stack([inc / 10000.0])
    if fe:
        ks = sorted(set(st))
        X = np.column_stack([X] + [(st == k).astype(float) for k in ks[1:]])
    b, _ = ols(y, X, st)
    fit = np.column_stack([np.ones(len(y)), X]) @ b
    resid = y - fit + y.mean()
    return resid, b[1]


def decile_gap(y, inc, hi, lo, q=10):
    """Within-income-decile Black-minus-white gap, pooled by decile size.

    Only deciles holding at least three ZIPs on each side contribute; the weight
    is the number of ZIPs in the decile that belong to either group.
    """
    edges = np.quantile(inc, np.linspace(0, 1, q + 1))
    edges[-1] += 1
    num = den = 0.0
    detail = []
    for i in range(q):
        m = (inc >= edges[i]) & (inc < edges[i + 1])
        h, l = m & hi, m & lo
        if h.sum() < 3 or l.sum() < 3:
            detail.append((i + 1, edges[i], h.sum(), l.sum(), None))
            continue
        g = y[h].mean() - y[l].mean()
        w = h.sum() + l.sum()
        num += g * w
        den += w
        detail.append((i + 1, edges[i], h.sum(), l.sum(), g))
    return (num / den if den else float("nan")), detail


def matched_gap(y, inc, hi_m, lo_m):
    """Nearest-neighbour income match, with replacement, inside a $2,000 caliper."""
    hi = np.where(hi_m)[0]
    lo = np.where(lo_m)[0]
    d, n = [], 0
    for i in hi:
        j = lo[np.argmin(np.abs(inc[lo] - inc[i]))]
        if abs(inc[j] - inc[i]) <= CALIPER:
            d.append(y[i] - y[j])
            n += 1
    return (np.mean(d) if d else float("nan")), n, len(hi)


def decile_levels(y, inc, q=10):
    """Price with each ZIP's own income decile mean removed, grand mean added back.

    The nonparametric twin of adjusted_levels: no slope is fitted, so a price-income
    relationship that bends does not get forced through a line.
    """
    edges = np.quantile(inc, np.linspace(0, 1, q + 1))
    edges[-1] += 1
    out = y.copy().astype(float)
    for i in range(q):
        m = (inc >= edges[i]) & (inc < edges[i + 1])
        if m.sum():
            out[m] = y[m] - y[m].mean()
    return out + y.mean()


def report(S, keys, label):
    blk = np.array([r["blk"] for r in S])
    wht = np.array([r["wht"] for r in S])
    inc = np.array([r["inc"] for r in S])
    st = np.array([r["st"] for r in S])
    print(f"\n{'='*74}\n{label}  ({len(S)} ZIPs, {len(set(st))} states)\n{'='*74}")

    print("\n-- 1. Price by racial composition, raw and with income held equal --\n")
    hdr = f"  {'group':<15}{'n':>5}{'income':>10}"
    for nm, _ in keys:
        hdr += f"{nm+' raw':>14}{nm+' adj':>14}"
    print(hdr)
    adj = {}
    for nm, key in keys:
        y = np.array([r[key] for r in S])
        adj[nm] = adjusted_levels(y, inc, st, blk)[0]
    for gname, m in groups(blk):
        if m.sum() == 0:
            continue
        line = f"  {gname:<15}{m.sum():>5}{inc[m].mean():>10,.0f}"
        for nm, key in keys:
            y = np.array([r[key] for r in S])
            line += f"{y[m].mean():>14.3f}{adj[nm][m].mean():>14.3f}"
        print(line)
    print("\n-- 1b. The same, equalising income nonparametrically by decile --\n")
    print(f"  {'group':<15}{'n':>5}" + "".join(f"{nm+' dec-adj':>18}" for nm, _ in keys))
    dec = {}
    for nm, key in keys:
        y = np.array([r[key] for r in S])
        dec[nm] = decile_levels(y, inc)
    for gname, m in groups(blk):
        if m.sum() == 0:
            continue
        print(f"  {gname:<15}{m.sum():>5}"
              + "".join(f"{dec[nm][m].mean():>18.3f}" for nm, _ in keys))
    for cname, sel in CONTRASTS:
        hi, lo = sel(blk, wht)
        print()
        for nm, _ in keys:
            g = dec[nm][hi].mean() - dec[nm][lo].mean()
            d = np.where(hi, 1.0, 0.0)[hi | lo]
            b, se = ols(dec[nm][hi | lo], np.column_stack([d]), st[hi | lo])
            print(f"  {nm}, {cname}, decile-adjusted: {g:+.3f} "
                  f"(clustered t {b[1]/se[1]:+.2f})")

    print("\n  'adj' is the price the group would pay at the sample-average income")
    print(f"  of ${inc.mean():,.0f}. Raw and adjusted columns are on the same scale.")

    print("\n-- 2. Four ways of equalising income, both definitions --\n")
    detail = None
    for cname, sel in CONTRASTS:
        hi, lo = sel(blk, wht)
        print(f"  {cname}   (n {hi.sum()} vs {lo.sum()})")
        print(f"  {'method':<34}" + "".join(f"{nm:>16}" for nm, _ in keys))
        rows = {}
        for nm, key in keys:
            y = np.array([r[key] for r in S])
            raw = y[hi].mean() - y[lo].mean()
            a1, slope = adjusted_levels(y, inc, st, blk)
            dec, det = decile_gap(y, inc, hi, lo)
            mat, matched, nh = matched_gap(y, inc, hi, lo)
            a4, _ = adjusted_levels(y, inc, st, blk, fe=True)
            rows[nm] = (raw, a1[hi].mean() - a1[lo].mean(), dec, mat,
                        a4[hi].mean() - a4[lo].mean(), slope, matched, nh)
            if nm == keys[0][0] and detail is None:
                detail = det
        for i2, lab in enumerate(["raw, no adjustment",
                                  "1. linear income adjustment",
                                  "2. within income decile",
                                  "3. matched on income (+/-$2k)",
                                  "4. linear income + state FE"]):
            print(f"  {lab:<34}"
                  + "".join(f"{rows[nm][i2]:>+16.3f}" for nm, _ in keys))
        print(f"  {'income gap between groups':<34}"
              f"{inc[hi].mean() - inc[lo].mean():>+16,.0f}")
        for nm, _ in keys:
            r = rows[nm]
            print(f"    {nm}: income slope {r[5]:+.4f}/gal per $10k; "
                  f"{r[6]} of {r[7]} high-Black ZIPs matched inside the caliper")
        print()

    print("\n-- 3. Within-decile detail (Walmart, majority definition) --\n")
    print(f"  {'decile':<8}{'income from':>13}{'n hi':>7}{'n lo':>7}{'gap':>10}")
    for d, e, nh, nl, g in detail:
        print(f"  {d:<8}{e:>13,.0f}{nh:>7}{nl:>7}"
              f"{(f'{g:+.3f}' if g is not None else 'too few'):>10}")


def exposure(S, label, keys=(("Walmart", "p"),)):
    """Where each group sits in the rural income distribution.

    Equalising income answers "same income, same price?". This answers the
    question that makes the first one matter: the groups are not at the same
    income, and the high-price end of the distribution is where one of them is.
    """
    blk = np.array([r["blk"] for r in S])
    wht = np.array([r["wht"] for r in S])
    inc = np.array([r["inc"] for r in S])
    ys = {nm: np.array([r[k] for r in S]) for nm, k in keys}
    y = ys[keys[0][0]]
    q = np.quantile(inc, np.linspace(0, 1, 11))
    q[-1] += 1
    dec = np.searchsorted(q, inc, side="right") - 1
    print(f"\n-- 4. Income-decile exposure, {label} --\n")
    print(f"  {'decile':<8}{'income from':>13}"
          + "".join(f"{nm:>11}" for nm, _ in keys)
          + f"{'% of maj-Black ZIPs':>22}{'% of maj-white ZIPs':>22}")
    mb, mw = blk >= 50, wht >= 50
    for i in range(10):
        m = dec == i
        print(f"  {i+1:<8}{q[i]:>13,.0f}"
              + "".join(f"{ys[nm][m].mean():>11.3f}" for nm, _ in keys)
              + f"{100*(m & mb).sum()/mb.sum():>21.1f}%"
              f"{100*(m & mw).sum()/mw.sum():>21.1f}%")
    b2 = dec <= 1
    print(f"\n  bottom two deciles hold {100*(b2 & mb).sum()/mb.sum():.1f}% of "
          f"majority-Black ZIPs and {100*(b2 & mw).sum()/mw.sum():.1f}% of "
          f"majority-white ones.")
    for nm, _ in keys:
        print(f"  {nm}: {ys[nm][b2].mean():.3f} there against "
              f"{ys[nm][~b2].mean():.3f} in the other eight "
              f"({ys[nm][b2].mean() - ys[nm][~b2].mean():+.3f}).")
    if len(keys) == 2:
        a, b = (ys[nm] for nm, _ in keys)
        print(f"\n  {keys[0][0]} minus {keys[1][0]}, by decile:")
        print("  " + "".join(f"{(a[dec==i]).mean()-(b[dec==i]).mean():>8.3f}"
                             for i in range(10)))
        print(f"  The spread is {a[dec==0].mean()-b[dec==0].mean():.3f} in the "
              f"poorest decile and {a[dec==9].mean()-b[dec==9].mean():.3f} in the "
              f"richest, on the same ZIPs.")
    print("\n  The exposure argument needs BOTH: a group concentrated in the low")
    print("  deciles, and a price that actually rises as income falls. The second")
    print("  condition is a property of the retailer, not of the geography.")


def coverage():
    """Which rural Walmart ZIPs got an Aldi price, and are they a racial sample?

    The Walmart-vs-Aldi contrast is run on identical ZIPs, so this does not bias
    it. It does bound what the Aldi column alone can be read as describing.
    """
    full, both = rural(), rural(both=True)
    have = {r["zip"] for r in both}
    miss = [r for r in full if r["zip"] not in have]
    print(f"\n-- 5. Aldi coverage of the rural Walmart panel --\n")
    print(f"  {len(both)} of {len(full)} rural Walmart ZIPs carry an Aldi price "
          f"({100*len(both)/len(full):.0f}%).")
    for lab, rows in (("with Aldi", both), ("without", miss)):
        b = np.array([r["blk"] for r in rows])
        print(f"  {lab:<10}n {len(rows):>5}   mean %Black {b.mean():>5.1f}"
              f"   majority Black {100*(b>=50).mean():>4.1f}%"
              f"   mean income {np.mean([r['inc'] for r in rows]):>8,.0f}")
    print("  Aldi's own footprint is not a random sample of rural America, so the")
    print("  Aldi column describes rural ZIPs Aldi chose to enter. Every")
    print("  Walmart/Aldi comparison above is run on the shared ZIPs only.")


def main():
    report(rural(), [("Walmart", "p")],
           "RURAL, full Walmart panel")
    exposure(rural(), "rural Walmart panel")
    both = rural(both=True)
    report(both, [("Walmart", "p"), ("Aldi", "aldi")],
           "RURAL, ZIPs carrying both retailers")
    exposure(both, "rural ZIPs carrying both retailers",
             keys=(("Walmart", "p"), ("Aldi", "aldi")))
    coverage()


if __name__ == "__main__":
    main()
