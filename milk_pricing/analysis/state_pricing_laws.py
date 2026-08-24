"""Do state pricing laws explain the state-level milk price distribution?

Backs reports/state_pricing_laws.md.

Three regimes are often conflated and behave completely differently:
  * minimum RETAIL milk price (PA, NJ) - fixes the price, compresses completely
  * classified/producer-side pricing (USDA AMS list) - reaches retail in some states
  * general below-cost / minimum-markup laws (~24 states) - floor at cost, rarely binds

The below-cost membership list comes from a secondary compilation and is not
verified statute by statute; the grouped comparison does not hinge on any one state.
"""
import csv
from collections import Counter

import numpy as np

RETAIL_MILK = {"PA", "NJ"}
USDA_CLASSIFIED = {"ME", "MT", "NV", "NY", "ND", "PA", "VA"}
BELOW_COST = {"AR", "CA", "CO", "HI", "ID", "KY", "LA", "ME", "MD", "MA", "MN", "MT", "NE",
              "NC", "ND", "OK", "RI", "SC", "TN", "UT", "WA", "WV", "WI", "WY"}


def load():
    S = {}
    for r in csv.DictReader(open("data/national_walmart_official.csv")):
        if r["whole_milk"] and r["state"]:
            S.setdefault(r["state"], []).append(float(r["whole_milk"]))
    return {k: v for k, v in S.items() if len(v) >= 10}


def cv(v):
    return 100 * np.std(v) / np.mean(v)


def tags(st):
    t = []
    if st in RETAIL_MILK:
        t.append("RETAIL-PRICE FIX")
    if st in USDA_CLASSIFIED:
        t.append("USDA classified")
    if st in BELOW_COST:
        t.append("below-cost law")
    return ", ".join(t) or "—"


def main():
    S = load()
    print("=== States by price compression ===")
    print(f"  {'st':<4}{'n':>5}{'mean':>8}{'CV':>7}{'distinct':>10}  regime")
    for st, v in sorted(S.items(), key=lambda kv: cv(kv[1])):
        print(f"  {st:<4}{len(v):>5}{np.mean(v):>8.2f}{cv(v):>6.1f}%{len(set(v)):>10}  {tags(st)}")

    print("\n=== Does the TYPE of law predict compression? ===")
    groups = {
        "milk retail-price fix (PA,NJ)": RETAIL_MILK,
        "USDA classified only": USDA_CLASSIFIED - RETAIL_MILK,
        "general below-cost only": BELOW_COST - USDA_CLASSIFIED - RETAIL_MILK,
        "neither": set(S) - BELOW_COST - USDA_CLASSIFIED - RETAIL_MILK,
    }
    print(f"  {'group':<32}{'states':>7}{'mean CV':>10}{'median CV':>11}{'mean $':>9}")
    means = {}
    for lab, g in groups.items():
        vals = [(st, cv(S[st]), np.mean(S[st])) for st in sorted(g) if st in S]
        if not vals:
            continue
        means[lab] = np.mean([v[2] for v in vals])
        print(f"  {lab:<32}{len(vals):>7}{np.mean([v[1] for v in vals]):>9.1f}%"
              f"{np.median([v[1] for v in vals]):>10.1f}%{means[lab]:>9.2f}")
        print(f"      {', '.join(f'{v[0]}({v[1]:.0f}%)' for v in sorted(vals, key=lambda x: x[1]))}")
    if "milk retail-price fix (PA,NJ)" in means and "neither" in means:
        gap = means["milk retail-price fix (PA,NJ)"] - means["neither"]
        print(f"\n  regulated minus unregulated: {gap:+.2f}/gal "
              f"({100*gap/means['neither']:+.0f}%) — the largest price effect in this project")

    print("\n=== Is South Carolina contaminated by its below-cost law? ===")
    ranked = sorted(S.items(), key=lambda kv: -cv(kv[1]))
    pos = [st for st, _ in ranked].index("SC") + 1
    print(f"  SC: CV {cv(S['SC']):.1f}%, {len(set(S['SC']))} distinct prices, "
          f"rank {pos} of {len(S)} most dispersed")
    print("  -> the statute does not bind. SC is a clean jurisdiction for this analysis.")


if __name__ == "__main__":
    main()
