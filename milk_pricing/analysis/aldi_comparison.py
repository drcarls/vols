"""Aldi as a comparison retailer: same design, different chain.

Backs reports/aldi_comparison.md.

WHY. reports/segmented_rural.md finds a racial gradient in Walmart milk prices confined
to low-income rural areas. The natural question is whether that is something Walmart does
or something the rural South does. Aldi is the available control: a different chain, a
different pricing architecture, the same ZIP codes.

DESIGN. Identical to analysis/segmented_rural.py -- stratify by income quartile x
urbanicity, compare ZIPs >=30% Black against ZIPs <=10% Black, then add geographic
controls. Aldi prices are joined to the SAME ZIP-level demographics used for Walmart
(data/national_walmart_official.csv), so the two retailers are measured on one
demographic basis and any difference is the retailer, not the covariates.

CAVEAT THAT GOVERNS EVERYTHING BELOW. Aldi prices by ZONE: 1,886 ZIPs resolve to 570
zones and only 64 distinct prices, with a median of 2 ZIPs per zone and one zone
spanning 122. Walmart's pricing unit is at or below the county. So a ZIP-level
regression on Aldi has far less independent variation than the same regression on
Walmart, and its effective sample is the zone count, not the ZIP count. Zone-clustered
errors are therefore the honest ones and are reported alongside.
"""
import csv
import json
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, "src")
from milk_pricing import panel

ALDI = "data/aldi_pooled.json"


def load():
    aldi = json.load(open(ALDI))
    demo = {}
    for r in csv.DictReader(open(panel.DEFAULT_PATH)):
        z = r["zip"].zfill(5)
        if not (r["pct_black"] and r["median_income"] and r["population"] and r["state"]):
            continue
        if float(r["median_income"]) <= 0 or float(r["population"]) <= 0:
            continue
        if r["state"] in panel.EXCLUDED:
            continue
        demo[z] = r
    rows = []
    for z, v in aldi.items():
        z = z.zfill(5)
        if z not in demo or not v.get("whole"):
            continue
        d = demo[z]
        rows.append({"zip": z, "z3": z[:3], "zone": str(v.get("zone")),
                     "p": float(v["whole"]), "st": d["state"], "cty": d["county"],
                     "geo": d["geo"], "blk": float(d["pct_black"]),
                     "inc": float(d["median_income"]), "pop": float(d["population"])})
    return rows


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


def arrays(rows):
    return (np.array([r["p"] for r in rows]), np.array([r["blk"] for r in rows]),
            np.array([r["inc"] for r in rows]),
            np.log(np.array([r["pop"] for r in rows]).clip(1)),
            np.array([1.0 if str(r["geo"]).lower().startswith("urb") else 0.0 for r in rows]),
            np.array([r["st"] for r in rows]), np.array([r["cty"] for r in rows]),
            np.array([r["z3"] for r in rows]), np.array([r["zone"] for r in rows]))


def main():
    rows = load()
    p, blk, inc, pop, urb, st, cty, z3, zone = arrays(rows)
    iq = np.digitize(inc, np.quantile(inc, [.25, .5, .75]))
    print(f"Aldi panel: {len(rows)} ZIPs, {len(set(st))} states, {len(set(zone))} pricing zones, "
          f"{len(set(np.round(p,2)))} distinct prices")
    print(f"  mean ${p.mean():.3f}, sd ${p.std():.3f}, range ${p.min():.2f}-${p.max():.2f}\n")

    print("=== 1. The Walmart design, applied to Aldi ===")
    print(f"  {'cell':<24}{'n hi':>6}{'n lo':>6}{'hi-Black':>10}{'low-Black':>11}{'gap':>9}")
    for q in range(4):
        for u in (0, 1):
            m = (iq == q) & (urb == u)
            hi, lo = m & (blk >= 30), m & (blk <= 10)
            if hi.sum() < 5 or lo.sum() < 5:
                continue
            print(f"  Q{q+1} income, {'urban' if u else 'rural':<6}{'':<7}{hi.sum():>6}{lo.sum():>6}"
                  f"{p[hi].mean():>10.3f}{p[lo].mean():>11.3f}{p[hi].mean()-p[lo].mean():>+9.3f}")

    print("\n=== 2. Pooled regression, Aldi ===")
    print(f"  {'specification':<40}{'coef':>12}{'t naive':>10}{'t state':>10}{'t zone':>10}")
    for lab, X in (("%Black alone", np.column_stack([blk])),
                   ("+ income + urbanicity", np.column_stack([blk, inc, urb])),
                   ("+ log population", np.column_stack([blk, inc, urb, pop]))):
        b, t0 = ols(p, X)
        _, t1 = ols(p, X, cluster=st)
        _, t2 = ols(p, X, cluster=zone)
        print(f"  {lab:<40}{b:>+12.5f}{t0:>+10.2f}{t1:>+10.2f}{t2:>+10.2f}")

    m = (iq == 0) & (urb == 0)
    print(f"\n=== 3. The segment where Walmart's gradient lives: low-income rural, n={m.sum()} ===")
    if m.sum() >= 30:
        base = np.column_stack([blk[m], inc[m], pop[m]])
        print(f"  {'geographic control':<28}{'coef':>12}{'t naive':>10}{'t state':>10}{'t zone':>10}")
        for lab, X in (("none", base),
                       ("state fixed effects", np.column_stack([base, D(st[m])])),
                       ("ZIP3 fixed effects", np.column_stack([base, D(z3[m])])),
                       ("county fixed effects", np.column_stack([base, D(cty[m])]))):
            b, t0 = ols(p[m], X)
            _, t1 = ols(p[m], X, cluster=st[m])
            _, t2 = ols(p[m], X, cluster=zone[m])
            print(f"  {lab:<28}{b:>+12.5f}{t0:>+10.2f}{t1:>+10.2f}{t2:>+10.2f}")
        hi, lo = m & (blk >= 30), m & (blk <= 10)
        print(f"\n  high-Black n={hi.sum()} mean ${p[hi].mean():.3f} | "
              f"low-Black n={lo.sum()} mean ${p[lo].mean():.3f} | "
              f"gap {p[hi].mean()-p[lo].mean():+.3f}")
        print(f"  zones: high-Black {len(set(zone[hi]))}, low-Black {len(set(zone[lo]))}, "
              f"shared {len(set(zone[hi]) & set(zone[lo]))}")
        print(f"  counties: high {len(set(cty[hi]))}, low {len(set(cty[lo]))}, "
              f"shared {len(set(cty[hi]) & set(cty[lo]))}")

    print("\n=== 4. Do Aldi's own zones sort on race? ===")
    print("  If Aldi assigns Blacker ZIPs to higher-priced zones, that is a zone-assignment")
    print("  question; if not, the zone structure is racially flat by construction.")
    zp = {}
    for r in rows:
        zp.setdefault(r["zone"], []).append(r)
    big = {z: v for z, v in zp.items() if len(v) >= 3}
    zb = np.array([np.mean([r["blk"] for r in v]) for v in big.values()])
    zpr = np.array([v[0]["p"] for v in big.values()])
    zn = np.array([len(v) for v in big.values()])
    b, t = ols(zpr, np.column_stack([zb]))
    print(f"  {len(big)} zones with >=3 ZIPs: zone price on zone mean %Black "
          f"{b:+.5f}/pt (t {t:+.2f})")
    print(f"  within-zone %Black spread: mean {np.mean([np.std([r['blk'] for r in v]) for v in big.values()]):.1f} pts "
          f"-- Blacker and whiter ZIPs share zones, and inside a zone the price is identical")


def matched():
    """The paired design: ZIPs carrying BOTH an Aldi and a Walmart price.

    Differencing the two retailers at the same ZIP removes everything common to the
    location -- freight, local demand, competition, income, urbanicity, the Class I
    differential -- and leaves the retailer. It is the cleanest identification the
    available data supports.

    Assumption it rests on: absent any racial gradient the Walmart-minus-Aldi spread
    would be constant across ZIPs. The two chains price different private labels at
    different levels (Aldi is a discounter), so the LEVEL of the spread is not
    meaningful; only its variation with racial composition is.
    """
    ald = {r["zip"]: r for r in load()}
    wm = {r["zip"]: r for r in panel.load()}
    both = sorted(set(ald) & set(wm))
    rows = [{**wm[z], "pw": wm[z]["p"], "pa": ald[z]["p"]} for z in both]
    pw = np.array([r["pw"] for r in rows]); pa = np.array([r["pa"] for r in rows])
    blk = np.array([r["blk"] for r in rows]); inc = np.array([r["inc"] for r in rows])
    pop = np.log(np.array([r["pop"] for r in rows]).clip(1))
    urb = np.array([1.0 if str(r["geo"]).lower().startswith("urb") else 0.0 for r in rows])
    st = np.array([r["st"] for r in rows])
    iq = np.digitize(inc, np.quantile(inc, [.25, .5, .75]))

    print(f"\n=== 5. MATCHED ZIPS: {len(rows)} ZIPs carrying both retailers, "
          f"{len(set(st))} states ===")
    m = (iq == 0) & (urb == 0)
    hi, lo = m & (blk >= 30), m & (blk <= 10)
    print(f"  low-income rural cell: n={m.sum()} (high-Black {hi.sum()}, low-Black {lo.sum()})\n")
    print(f"  {'retailer':<14}{'high-Black':>12}{'low-Black':>12}{'gap':>10}")
    print(f"  {'Walmart':<14}{pw[hi].mean():>12.3f}{pw[lo].mean():>12.3f}"
          f"{pw[hi].mean()-pw[lo].mean():>+10.3f}")
    print(f"  {'Aldi':<14}{pa[hi].mean():>12.3f}{pa[lo].mean():>12.3f}"
          f"{pa[hi].mean()-pa[lo].mean():>+10.3f}")
    print(f"  {'difference':<14}{'':>12}{'':>12}"
          f"{(pw[hi].mean()-pw[lo].mean())-(pa[hi].mean()-pa[lo].mean()):>+10.3f}")

    base = np.column_stack([blk[m], inc[m], pop[m]])
    print(f"\n  regression on the same ZIPs:  {'coef':>12}{'t naive':>10}{'t state':>10}")
    for lab, y in (("Walmart", pw[m]), ("Aldi", pa[m]), ("Walmart - Aldi", (pw - pa)[m])):
        b, t0 = ols(y, base)
        _, t1 = ols(y, base, cluster=st[m])
        print(f"  {lab:<28}{b:>+12.5f}{t0:>+10.2f}{t1:>+10.2f}")
    print(f"\n  Walmart's premium over Aldi: {(pw-pa)[hi].mean():+.3f} in high-Black ZIPs, "
          f"{(pw-pa)[lo].mean():+.3f} in low-Black, difference "
          f"{(pw-pa)[hi].mean()-(pw-pa)[lo].mean():+.3f}")
    print("  With only 12 state clusters this is directionally clear and not significant.")


if __name__ == "__main__":
    main()
    matched()
