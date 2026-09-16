"""The comparison done inside each state, with within-state income and race cuts.

Backs reports/within_state_design.md. Written after the client pointed out that
Mississippi has low-Black rural ZIPs, which the earlier design was not using.

THE FLAW THIS FIXES. analysis/segmented_rural.py stratifies on NATIONAL income quartiles
and absolute racial thresholds (>=30% Black against <=10%). Both choices select on state:

  * A national income cut keeps 59% of Mississippi's rural ZIPs but 26% of Texas's,
    because Mississippi is poorer. So "low-income rural" is disproportionately drawn
    from poor states, which are disproportionately Black.
  * A <=10% Black threshold is near-unsatisfiable in Mississippi (4 rural ZIPs in the
    whole panel) and easy in Tennessee. So the low-Black comparison group is drawn from
    different states than the high-Black group by construction.

Together they build the confound into the design: the contrast is mostly between states
even before any price is looked at. This script instead ranks ZIPs WITHIN their own
state, so every comparison is between rural ZIPs of the same state at similar positions
in that state's own income and racial distributions.
"""
import csv
import json
import sys

import numpy as np

sys.path.insert(0, "src")
from milk_pricing import panel


def load():
    wm = [r for r in panel.load() if not str(r["geo"]).lower().startswith("urb")]
    sep = {json.loads(l)["zip"].zfill(5): json.loads(l) for l in open("data/aldi_2026_09.jsonl")}
    for r in wm:
        v = sep.get(r["zip"])
        r["aldi"] = float(v["whole"]) if v and v.get("whole") is not None else None
    return wm


def state_cells(rows, inc_keep=0.5, blk_q=0.33):
    """Within each state: keep the poorer half of rural ZIPs, then split the
    remaining ZIPs into the top and bottom thirds of that state's Black share."""
    out = {}
    by = {}
    for r in rows:
        by.setdefault(r["st"], []).append(r)
    for st, g in by.items():
        if len(g) < 12:
            continue
        inc_cut = np.quantile([x["inc"] for x in g], inc_keep)
        poor = [x for x in g if x["inc"] <= inc_cut]
        if len(poor) < 8:
            continue
        b = np.array([x["blk"] for x in poor])
        lo_cut, hi_cut = np.quantile(b, [blk_q, 1 - blk_q])
        if hi_cut - lo_cut < 3:          # no meaningful racial spread to compare
            continue
        hi = [x for x in poor if x["blk"] >= hi_cut]
        lo = [x for x in poor if x["blk"] <= lo_cut]
        if len(hi) >= 4 and len(lo) >= 4:
            out[st] = (hi, lo)
    return out


def gap(hi, lo, key):
    h = [x[key] for x in hi if x.get(key) is not None]
    l = [x[key] for x in lo if x.get(key) is not None]
    if len(h) < 4 or len(l) < 4:
        return None, len(h), len(l)
    return float(np.mean(h) - np.mean(l)), len(h), len(l)


def main():
    rows = load()
    cells = state_cells(rows)
    print(f"{len(rows)} rural ZIPs; {len(cells)} states support a within-state comparison\n")
    print("Within each state: poorer half of its rural ZIPs, then top vs bottom third")
    print("of THAT state's Black share. Every contrast is inside one state.\n")
    print(f"  {'state':<7}{'n hi':>5}{'n lo':>5}{'%Blk hi':>9}{'%Blk lo':>9}"
          f"{'Walmart':>10}{'Aldi':>10}{'W - A':>9}")
    W, A, D = [], [], []
    for st in sorted(cells):
        hi, lo = cells[st]
        gw, nh, nl = gap(hi, lo, "p")
        ga, ah, al = gap(hi, lo, "aldi")
        bh = np.mean([x["blk"] for x in hi]); bl = np.mean([x["blk"] for x in lo])
        W.append((gw, nh + nl))
        line = (f"  {st:<7}{nh:>5}{nl:>5}{bh:>9.1f}{bl:>9.1f}{gw:>+10.3f}")
        if ga is not None:
            A.append((ga, ah + al)); D.append((gw - ga, min(nh + nl, ah + al)))
            line += f"{ga:>+10.3f}{gw-ga:>+9.3f}"
        else:
            line += f"{'-':>10}{'-':>9}"
        print(line)

    def wm_(xs):
        v = np.array([x[0] for x in xs]); w = np.array([x[1] for x in xs], float)
        return np.average(v, weights=w), (v > 0).sum(), len(v)

    print()
    for lab, xs in (("Walmart racial gap", W), ("Aldi racial gap", A),
                    ("Walmart minus Aldi", D)):
        if not xs:
            continue
        m, pos, n = wm_(xs)
        print(f"  {lab:<22} weighted mean {m:>+7.3f}/gal   positive in {pos}/{n} states")

    print("\n=== Same thing under the OLD design, for contrast ===")
    inc_all = np.array([r["inc"] for r in rows])
    q1 = np.quantile(inc_all, .25)
    oh = [r for r in rows if r["inc"] <= q1 and r["blk"] >= 30]
    ol = [r for r in rows if r["inc"] <= q1 and r["blk"] <= 10]
    from collections import Counter
    print(f"  national Q1 + absolute thresholds: {len(oh)} high-Black, {len(ol)} low-Black")
    print(f"    high-Black states: {Counter(r['st'] for r in oh).most_common(5)}")
    print(f"    low-Black  states: {Counter(r['st'] for r in ol).most_common(5)}")
    print(f"    pooled Walmart gap {np.mean([r['p'] for r in oh])-np.mean([r['p'] for r in ol]):+.3f}")
    print("  The two groups come from different states. The within-state design above")
    print("  compares ZIPs that share a state, an income position and a milk market.")


if __name__ == "__main__":
    main()
