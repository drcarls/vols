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


def decile_gap(y, inc, blk, hi_t=30.0, lo_t=10.0, q=10):
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
        hi, lo = m & (blk >= hi_t), m & (blk <= lo_t)
        if hi.sum() < 3 or lo.sum() < 3:
            detail.append((i + 1, edges[i], hi.sum(), lo.sum(), None))
            continue
        g = y[hi].mean() - y[lo].mean()
        w = hi.sum() + lo.sum()
        num += g * w
        den += w
        detail.append((i + 1, edges[i], hi.sum(), lo.sum(), g))
    return (num / den if den else float("nan")), detail


def matched_gap(y, inc, blk, hi_t=30.0, lo_t=10.0):
    """Nearest-neighbour income match, with replacement, inside a $2,000 caliper."""
    hi = np.where(blk >= hi_t)[0]
    lo = np.where(blk <= lo_t)[0]
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
    hi30, lo10 = blk >= 30, blk <= 10
    for nm, _ in keys:
        g = dec[nm][hi30].mean() - dec[nm][lo10].mean()
        d = np.where(hi30, 1.0, 0.0)[hi30 | lo10]
        b, se = ols(dec[nm][hi30 | lo10], np.column_stack([d]), st[hi30 | lo10])
        print(f"\n  {nm} >=30% vs <=10%, decile-adjusted: {g:+.3f} "
              f"(clustered t {b[1]/se[1]:+.2f})")

    print("\n  'adj' is the price the group would pay at the sample-average income")
    print(f"  of ${inc.mean():,.0f}. Raw and adjusted columns are on the same scale.")

    print("\n-- 2. The >=30% vs <=10% gap, four ways of equalising income --\n")
    print(f"  {'method':<34}" + "".join(f"{nm:>16}" for nm, _ in keys))
    hi, lo = blk >= 30, blk <= 10
    rows = {}
    for nm, key in keys:
        y = np.array([r[key] for r in S])
        raw = y[hi].mean() - y[lo].mean()
        a1, slope = adjusted_levels(y, inc, st, blk)
        lin = a1[hi].mean() - a1[lo].mean()
        dec, detail = decile_gap(y, inc, blk)
        mat, nm_, nh = matched_gap(y, inc, blk)
        a4, _ = adjusted_levels(y, inc, st, blk, fe=True)
        fe = a4[hi].mean() - a4[lo].mean()
        rows[nm] = (raw, lin, dec, mat, fe, slope, nm_, nh, detail)
    for i, lab in enumerate(["raw, no adjustment",
                             "1. linear income adjustment",
                             "2. within income decile",
                             "3. matched on income (+/-$2k)",
                             "4. linear income + state FE"]):
        print(f"  {lab:<34}" + "".join(f"{rows[nm][i]:>+16.3f}" for nm, _ in keys))
    print()
    for nm, _ in keys:
        r = rows[nm]
        print(f"  {nm}: income slope {r[5]:+.4f}/gal per $10k; "
              f"{r[6]} of {r[7]} high-Black ZIPs found a match inside the caliper")

    print("\n-- 3. Within-decile detail (Walmart) --\n")
    print(f"  {'decile':<8}{'income from':>13}{'n hi':>7}{'n lo':>7}{'gap':>10}")
    for d, e, nh, nl, g in rows[keys[0][0]][8]:
        print(f"  {d:<8}{e:>13,.0f}{nh:>7}{nl:>7}"
              f"{(f'{g:+.3f}' if g is not None else 'too few'):>10}")


def main():
    report(rural(), [("Walmart", "p")],
           "RURAL, full Walmart panel")
    report(rural(both=True), [("Walmart", "p"), ("Aldi", "aldi")],
           "RURAL, ZIPs carrying both retailers")


if __name__ == "__main__":
    main()
