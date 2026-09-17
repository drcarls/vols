"""Two ways to close the rural gap, and how well each one reaches Black families.

Backs reports/remedy_targeting.md.

WHY. The Aldi-slope counterfactual in reports/black_incidence.md is often read as
"Walmart could lower its price in high-Black rural areas". That is not what it
does. It flattens the price-INCOME gradient; the benefit lands on Black areas
because Black rural residents are concentrated at the bottom of the rural income
distribution, not because race enters the rule. The distinction matters both
legally - a race-conditioned price is a different thing to ask a court for - and
empirically, because the two remedies reach very different sets of people.

DESIGN. Price the same two policies over the rural panel and score each on:
  coverage  - what share of Black rural residents live somewhere it applies;
  incidence - how much of the Black/white person-weighted gap it removes;
  reach     - how much it delivers to the average Black rural resident, net of
              what white rural residents receive from the same policy, since a
              shared benefit removes no disparity (reports/black_incidence.md s4).
Feasibility is assessed against observed prices only: what Walmart already charges
in other rural ZIPs and what Aldi charges in the same ones. No cost or margin data
is available, so nothing here speaks to profitability.
"""
import json
import sys

import numpy as np

sys.path.insert(0, "src")
from milk_pricing import panel

SEP = "data/aldi_2026_09.jsonl"
GAL = 17.0


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
    return float(np.sum(y * w) / np.sum(w))


def score(lab, y0, y1, wb, ww):
    """Report a policy as coverage-free deltas: Black, white, and the difference."""
    db, dw = pw(y1, wb) - pw(y0, wb), pw(y1, ww) - pw(y0, ww)
    g0, g1 = pw(y0, wb) - pw(y0, ww), pw(y1, wb) - pw(y1, ww)
    print(f"  {lab:<34}{db*100:>+9.1f}c{dw*100:>+9.1f}c{(db-dw)*100:>+11.1f}c"
          f"{(db-dw)*GAL:>+10.2f}{100*(g0-g1)/g0:>10.0f}%")
    return db - dw


def main():
    S = rural()
    blk = np.array([r["blk"] for r in S])
    inc = np.array([r["inc"] for r in S])
    y = np.array([r["p"] for r in S])
    pop = np.array([r["pop"] for r in S])
    wb = pop * blk / 100.0
    ww = pop * np.array([r["wht"] for r in S]) / 100.0
    e = np.quantile(inc, np.linspace(0, 1, 11))
    e[-1] += 1
    d = np.searchsorted(e, inc, side="right") - 1

    print(f"RURAL PANEL: {len(S)} ZIPs, {np.sum(wb)/1e6:.2f}M Black residents\n")

    print("=== 1. Where Black rural residents actually live ===\n")
    print(f"  {'target set':<34}{'ZIPs':>7}{'% of Black rural res.':>24}"
          f"{'mean price':>12}")
    for lab, m in (("majority-Black ZIPs", blk >= 50),
                   (">=30% Black ZIPs", blk >= 30),
                   (">=20% Black ZIPs", blk >= 20),
                   ("bottom two income deciles", d <= 1),
                   ("bottom three income deciles", d <= 2)):
        print(f"  {lab:<34}{m.sum():>7}{100*wb[m].sum()/wb.sum():>23.1f}%"
              f"{y[m].mean():>12.3f}")
    print("\n  A race-targeted cut misses most Black rural residents, because most")
    print("  do not live in a majority-Black ZIP. An income-targeted cut reaches")
    print("  more of them AND is the rule the price data actually supports.")

    print("\n=== 2. Two policies, scored ===\n")
    print(f"  {'policy':<34}{'Black':>10}{'white':>10}{'disparity':>11}"
          f"{'$/yr':>10}{'gap closed':>11}")
    # (a) race-targeted: majority-Black rural ZIPs priced at the majority-white mean
    mb = blk >= 50
    mw = np.array([r["wht"] for r in S]) >= 50
    a = y.copy()
    a[mb] = y[mw].mean()
    score("cut majority-Black ZIPs to", y, a, wb, ww)
    print("    the majority-white mean")
    # (b) income-targeted: flatten the price-income gradient, pivot at mean income
    x = inc / 10000.0
    sw = np.polyfit(x, y, 1)[0]
    B = rural(both=True)
    xb = np.array([r["inc"] for r in B]) / 10000.0
    sa = np.polyfit(xb, np.array([r["aldi"] for r in B]), 1)[0]
    b = y + (sa - sw) * (x - x.mean())
    score("flatten income gradient to", y, b, wb, ww)
    print("    Aldi's slope")
    # (c) income-targeted, floor only: nobody below the mean income pays above
    #     the price the fitted line gives at the mean
    c = np.minimum(y, np.polyval(np.polyfit(x, y, 1), x.mean()))
    score("cap every rural ZIP at the", y, c, wb, ww)
    print("    mean-income fitted price")
    print("\n  'disparity' is Black minus white: the part of the benefit that is")
    print("  not also delivered to white rural residents. It is the only column")
    print("  that measures a remedy rather than a price cut.")

    print("\n=== 3. Is the lower price observed anywhere? ===\n")
    lo = d <= 1
    print(f"  Walmart, bottom two rural income deciles   {y[lo].mean():.3f}")
    print(f"  Walmart, top two rural income deciles      {y[d >= 8].mean():.3f}")
    Ba = np.array([r["aldi"] for r in B])
    Bi = np.array([r["inc"] for r in B])
    eb = np.quantile(Bi, np.linspace(0, 1, 11))
    eb[-1] += 1
    db_ = np.searchsorted(eb, Bi, side="right") - 1
    print(f"  Aldi, same bottom two deciles              {Ba[db_ <= 1].mean():.3f}")
    print("\n  Walmart already charges the lower price in richer rural ZIPs, and a")
    print("  competitor charges less again in these same poor rural ZIPs. That")
    print("  establishes the price point is achievable in these markets; it says")
    print("  nothing about margin, because no cost data is available.")


if __name__ == "__main__":
    main()
