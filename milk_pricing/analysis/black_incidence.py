"""Who bears the rural price gradient, counted in people rather than ZIPs.

Backs reports/black_incidence.md.

WHY. Everything in reports/income_adjusted.md is ZIP-level: it asks whether a ZIP
with more Black residents pays more than a ZIP with fewer, and the answer once
income is equal is close to no. That is the right test for "does the retailer
price by race". It is the wrong unit for "who bears the cost", which is a question
about people. A disparate-impact claim does not require a race-based rule; it
requires a facially neutral practice whose burden falls unequally. So this file
drops the ZIP as the unit and weights by residents.

DESIGN. Each ZIP contributes pop x %Black Black residents and pop x %White white
residents, each facing that ZIP's price. The statistic is the person-weighted mean
price faced by Black residents minus the same for white residents - the same
shift-invariant gap used in analysis/usdss.py, so retail and regulatory surfaces
stay comparable.

Three questions, in order:
  1. what price does the average Black rural resident face against the average
     white one, raw and with income equalised;
  2. how much of that incidence is the price-income gradient rather than anything
     race-specific, which is answered by flattening the gradient and re-running;
  3. what it costs, if Walmart's rural gradient were as flat as Aldi's on the
     same ZIPs.

CAVEAT carried into the report: the price is the one posted at the Walmart serving
that ZIP, so pairing it with residents assumes Black and white residents of a ZIP
shop the same store. Within a ZIP that is close to forced - there is one price -
but it does assume no systematic difference in where people actually buy.
"""
import json
import sys

import numpy as np

sys.path.insert(0, "src")
from milk_pricing import panel

SEP = "data/aldi_2026_09.jsonl"
GAL_PERSON_YR = 17.0        # USDA ERS per-capita fluid milk availability, gallons


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


def pw(y, w):
    """Person-weighted mean."""
    return float(np.sum(y * w) / np.sum(w))


def weights(S):
    pop = np.array([r["pop"] for r in S])
    return pop * np.array([r["blk"] for r in S]) / 100.0, \
           pop * np.array([r["wht"] for r in S]) / 100.0


def decile_adjust(y, inc, q=10):
    """Remove each income decile's mean price, add the grand mean back."""
    e = np.quantile(inc, np.linspace(0, 1, q + 1))
    e[-1] += 1
    out = y.astype(float).copy()
    for i in range(q):
        m = (inc >= e[i]) & (inc < e[i + 1])
        if m.sum():
            out[m] = y[m] - y[m].mean()
    return out + y.mean()


def main():
    S = rural()
    inc = np.array([r["inc"] for r in S])
    y = np.array([r["p"] for r in S])
    wb, ww = weights(S)
    print(f"RURAL WALMART PANEL: {len(S)} ZIPs, "
          f"{np.sum(wb)/1e6:.2f}M Black and {np.sum(ww)/1e6:.2f}M white residents\n")

    print("=== 1. Price faced by the average rural resident ===\n")
    print(f"  {'':<26}{'Black':>10}{'white':>10}{'gap':>10}")
    for lab, v in (("as posted", y), ("income equalised", decile_adjust(y, inc))):
        print(f"  {lab:<26}{pw(v, wb):>10.3f}{pw(v, ww):>10.3f}"
              f"{pw(v, wb) - pw(v, ww):>+10.3f}")
    raw = pw(y, wb) - pw(y, ww)
    adj = pw(decile_adjust(y, inc), wb) - pw(decile_adjust(y, inc), ww)
    print(f"\n  Of the {raw*100:.1f}c a Black rural resident pays above a white one,")
    print(f"  {(raw-adj)*100:.1f}c is the price-income gradient and {adj*100:.1f}c is not.")
    print("  The gradient part is not a smaller finding. It is the disparate impact:")
    print("  a facially neutral pricing practice, borne unequally.")

    print("\n=== 2. Where rural residents sit in the income distribution ===\n")
    e = np.quantile(inc, np.linspace(0, 1, 11))
    e[-1] += 1
    d = np.searchsorted(e, inc, side="right") - 1
    print(f"  {'decile':<8}{'income from':>13}{'mean price':>12}"
          f"{'% of Black rural':>18}{'% of white rural':>18}")
    for i in range(10):
        m = d == i
        print(f"  {i+1:<8}{e[i]:>13,.0f}{pw(y[m], np.ones(m.sum())):>12.3f}"
              f"{100*wb[m].sum()/wb.sum():>17.1f}%{100*ww[m].sum()/ww.sum():>17.1f}%")
    b2 = d <= 1
    print(f"\n  bottom two deciles: {100*wb[b2].sum()/wb.sum():.1f}% of Black rural "
          f"residents, {100*ww[b2].sum()/ww.sum():.1f}% of white rural residents "
          f"({wb[b2].sum()/ww[b2].sum()*100/(wb.sum()/ww.sum()*100):.1f}x)")

    print("\n=== 3. What a flatter gradient would be worth ===\n")
    B = rural(both=True)
    incb = np.array([r["inc"] for r in B])
    yw = np.array([r["p"] for r in B])
    ya = np.array([r["aldi"] for r in B])
    wbb, wwb = weights(B)
    sw = np.polyfit(incb / 10000.0, yw, 1)[0]
    sa = np.polyfit(incb / 10000.0, ya, 1)[0]
    print(f"  On the {len(B)} shared ZIPs, the price-income slope is "
          f"{sw:+.4f}/gal per $10k at Walmart and {sa:+.4f} at Aldi.")
    # counterfactual: Walmart keeps its level but adopts Aldi's slope
    cf = yw + (sa - sw) * (incb - incb.mean()) / 10000.0
    for lab, v in (("Walmart as posted", yw), ("Walmart at Aldi's slope", cf)):
        print(f"  {lab:<28}Black {pw(v, wbb):>6.3f}  white {pw(v, wwb):>6.3f}  "
              f"gap {pw(v, wbb)-pw(v, wwb):>+6.3f}")
    g0 = pw(yw, wbb) - pw(yw, wwb)
    g1 = pw(cf, wbb) - pw(cf, wwb)
    print(f"\n  Adopting Aldi's gradient - no change in average price level - "
          f"removes {100*(g0-g1)/g0:.0f}% of the")
    print(f"  Black/white incidence on these ZIPs ({g0*100:.1f}c to {g1*100:.1f}c).")

    print("\n=== 4. What it costs Black rural households ===\n")
    n_blk = np.sum(wb)
    for lab, g in (("as posted, vs white rural residents", raw),
                   ("attributable to the income gradient", raw - adj)):
        print(f"  {lab:<38}{g*GAL_PERSON_YR:>7.2f}/person/yr"
              f"{g*GAL_PERSON_YR*n_blk/1e6:>9.1f}M/yr in aggregate")
    print(f"\n  {GAL_PERSON_YR:.0f} gal/person/yr (USDA ERS per-capita fluid milk),")
    print(f"  {n_blk/1e6:.2f}M Black residents in the rural panel. Milk alone; the")
    print("  same gradient runs through the rest of the basket, untested here.")


if __name__ == "__main__":
    main()
