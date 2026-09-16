"""The September 2026 Aldi re-collection: is the shop the pricing unit, and does the
racial comparison hold on fresh data?

    python3 analysis/aldi_2026_09.py

Reads data/aldi_2026_09.jsonl (from analysis/aldi_collect.py) and answers, in order:

  1. Coverage and how the new prices compare to August.
  2. Is the SHOP the pricing unit? August recorded only a zone, and treating it as the
     pricing unit produced a false claim -- see reports/aldi_comparison.md section 4.
     This is the direct test the August data could not support.
  3. Does the milk carve-out hold at Aldi? The basket gives 26 dairy items per ZIP.
  4. Does the Walmart-vs-Aldi racial comparison survive on the new series?
"""
import csv
import json
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, "src")
from milk_pricing import panel

SRC = "data/aldi_2026_09.jsonl"


def load():
    rows = [json.loads(l) for l in open(SRC)]
    good = [r for r in rows if r.get("whole") is not None]
    demo = {r["zip"].zfill(5): r for r in csv.DictReader(open(panel.DEFAULT_PATH))}
    aug = json.load(open("data/aldi_pooled.json"))
    out = []
    for r in good:
        z = r["zip"].zfill(5)
        d = demo.get(z)
        if not d or d["state"] in panel.EXCLUDED:
            continue
        if not (d["pct_black"] and d["median_income"] and d["population"]):
            continue
        out.append({"zip": z, "shop": r.get("shop"), "zone": r.get("zone"),
                    "p": float(r["whole"]), "items": r.get("items", {}),
                    "aug": (aug.get(r["zip"]) or {}).get("whole"),
                    "st": d["state"], "cty": d["county"], "geo": d["geo"],
                    "blk": float(d["pct_black"]), "inc": float(d["median_income"]),
                    "pop": float(d["population"])})
    return rows, out


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
    return b[1], b[1] / np.sqrt(np.diag(V))[1]


def unit_test(rows, key, label):
    """Does `key` determine price? Report the share of units carrying >1 price."""
    by = defaultdict(set)
    for r in rows:
        if r.get(key):
            by[r[key]].add(round(r["p"], 2))
    if not by:
        return
    multi = {k: v for k, v in by.items() if len(v) > 1}
    span = max((max(v) - min(v)) for v in by.values())
    n_in_multi = sum(1 for r in rows if r.get(key) in multi)
    print(f"  {label:<22}{len(by):>7} units  {len(multi):>6} multi-price "
          f"({100*len(multi)/len(by):>4.0f}%)  widest ${span:.2f}  "
          f"{n_in_multi}/{len(rows)} ZIPs affected")


def main():
    raw, rows = load()
    err = [r for r in raw if r.get("error")]
    print(f"collected {len(raw)} ZIPs, {len(raw)-len(err)} priced, {len(err)} errors; "
          f"{len(rows)} usable after demographics and state exclusions")
    if err:
        from collections import Counter
        print("  errors:", Counter(str(e['error'])[:44] for e in err).most_common(3))

    p = np.array([r["p"] for r in rows])
    print(f"  price ${p.min():.2f}-${p.max():.2f}, mean ${p.mean():.3f}, sd ${p.std():.3f}, "
          f"{len(set(np.round(p,2)))} distinct values, {len({r['shop'] for r in rows})} shops\n")

    print("=== 1. What is the pricing unit? ===")
    unit_test(rows, "zone", "zone (Aug's field)")
    unit_test(rows, "shop", "shop")
    unit_test(rows, "cty", "county")
    unit_test(rows, "st", "state")
    print("  A unit that sets price should show ~0% multi-price.")

    paired = [r for r in rows if r["aug"] is not None]
    if paired:
        a = np.array([r["aug"] for r in paired]); b = np.array([r["p"] for r in paired])
        print(f"\n=== 2. Against August, {len(paired)} paired ZIPs ===")
        print(f"  Aug mean ${a.mean():.3f}  Sep mean ${b.mean():.3f}  "
              f"change {b.mean()-a.mean():+.3f}")
        print(f"  identical: {(np.abs(a-b)<0.005).sum()} ({100*(np.abs(a-b)<0.005).mean():.0f}%)   "
              f"correlation {np.corrcoef(a,b)[0,1]:+.3f}")

    print("\n=== 3. The milk carve-out at Aldi ===")
    byitem = defaultdict(list)
    for r in rows:
        for k, v in (r["items"] or {}).items():
            byitem[k].append(v)
    big = {k: v for k, v in byitem.items() if len(v) >= 0.5 * len(rows)}
    print(f"  {'item':<50}{'n':>6}{'distinct':>10}{'sd':>8}")
    for k, v in sorted(big.items(), key=lambda kv: -len(set(np.round(kv[1], 2))))[:14]:
        print(f"  {k[:49]:<50}{len(v):>6}{len(set(np.round(v,2))):>10}{np.std(v):>8.3f}")

    print("\n=== 4. Racial comparison on the new series ===")
    wm = {r["zip"]: r for r in panel.load()}
    both = [r for r in rows if r["zip"] in wm]
    print(f"  {len(both)} ZIPs with both retailers")
    blk = np.array([r["blk"] for r in both]); inc = np.array([r["inc"] for r in both])
    pop = np.log(np.array([r["pop"] for r in both]).clip(1))
    urb = np.array([1.0 if str(r["geo"]).lower().startswith("urb") else 0.0 for r in both])
    st = np.array([r["st"] for r in both])
    pa = np.array([r["p"] for r in both]); pw = np.array([wm[r["zip"]]["p"] for r in both])
    iq = np.digitize(inc, np.quantile(inc, [.25, .5, .75]))
    m = (iq == 0) & (urb == 0)
    hi, lo = m & (blk >= 30), m & (blk <= 10)
    print(f"  low-income rural: n={m.sum()} (high-Black {hi.sum()}, low-Black {lo.sum()})")
    if hi.sum() >= 5 and lo.sum() >= 5:
        print(f"  {'retailer':<22}{'high-Black':>12}{'low-Black':>12}{'gap':>10}")
        print(f"  {'Walmart (Aug)':<22}{pw[hi].mean():>12.3f}{pw[lo].mean():>12.3f}"
              f"{pw[hi].mean()-pw[lo].mean():>+10.3f}")
        print(f"  {'Aldi (Sep, fresh)':<22}{pa[hi].mean():>12.3f}{pa[lo].mean():>12.3f}"
              f"{pa[hi].mean()-pa[lo].mean():>+10.3f}")
        print(f"  {'difference':<22}{'':>12}{'':>12}"
              f"{(pw[hi].mean()-pw[lo].mean())-(pa[hi].mean()-pa[lo].mean()):>+10.3f}")
        base = np.column_stack([blk[m], inc[m], pop[m]])
        print(f"\n  {'':<22}{'coef':>12}{'t naive':>10}{'t state':>10}")
        for lab, y in (("Walmart", pw[m]), ("Aldi (Sep)", pa[m]), ("Walmart - Aldi", (pw-pa)[m])):
            c, t0 = ols(y, base); _, t1 = ols(y, base, cluster=st[m])
            print(f"  {lab:<22}{c:>+12.5f}{t0:>+10.2f}{t1:>+10.2f}")


if __name__ == "__main__":
    main()
