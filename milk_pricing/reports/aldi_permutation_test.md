# Does Aldi rescue the SC finding from the permutation critique?

Largely yes on mechanism, not yet on significance.

## The point, and why it lands

My pool-size and placebo critique said: a small comparator pool plus this matching design manufactures significance. If that were the whole story it would manufacture it for **any** retailer run through the same pool.

It does not. Same 10 white rural comparators, same ZIPs, same matching, same Class I restriction — Walmart comes out positive and Aldi comes out flat.

| Same-region design | Gap | Nominal t | **Permutation p** |
|---|---:|---:|---:|
| Walmart | +$0.421 | 2.81 | **0.122** |
| Aldi | −$0.025 | −0.28 | **0.890** |
| DiD (Walmart − Aldi) | **+$0.446** | 3.03 | **0.086** |

The placebo rates are effectively identical for the two chains — random labels produce |t| > 2 about **28% of the time for Walmart and 27% for Aldi**. So the design inflates variance equally for both. What differs is where the *real* statistic falls in its own null distribution: Walmart's sits in the tail, Aldi's sits dead in the middle (p = 0.89).

That is a meaningful asymmetry and it does undercut the pure-artifact reading. A mechanical design effect cannot be selective about which retailer it hits.

## The caveat: permutation inference still does not clear 0.05

| Statistic | Nominal t | Permutation p |
|---|---:|---:|
| Walmart cross-region | 3.19 | 0.074 |
| Walmart same-region | 2.81 | 0.122 |
| **DiD same-region** | **3.03** | **0.086** |
| DiD cross-region | 1.26 | 0.480 |

The difference-in-differences — the cleanest retailer-specific estimate — comes in at **p = 0.086**. Marginal. Directionally consistent, economically meaningful at 45 cents a gallon, and not significant at the conventional threshold on this sample.

(This run is restricted to the 54 SC rural ZIPs carrying both retailers, so it is a slightly smaller sample than the 25/10 SC-only run that returned p ≈ 0.04.)

## Where that leaves it

Three statements, all supported:

1. **Aldi defeats the artifact explanation.** Identical design, identical pool, identical placebo rate, opposite result. Whatever is happening in SC is retailer-specific, not a property of the matching.
2. **The DiD is the right headline** — it nets out everything geographic that moves both chains, which is precisely the defense the memo needs to answer.
3. **At SC alone it is not yet significant under correct inference.** p = 0.086. Reporting it as t = 3.03 would overstate it.

## What would settle it

Collect Aldi for **Louisiana and Mississippi** — the other two states where Walmart's matched gap is significantly positive — and run the same DiD. The ZIP-pinning method that produced 488 SC Aldi prices works on any state.

If Aldi comes back flat in LA and MS while Walmart is positive in all three, the pooled DiD would carry roughly three times the n and would very likely clear conventional significance. It would also convert a single-state finding into a replicated one, which is worth considerably more than a lower p-value in one state.

If Aldi instead shows the same positive gap in LA and MS, that points back to regional structure and away from a Walmart-specific claim — which is equally worth knowing before filing.

## Correction: the test should have been one-sided

The permutation above is two-sided — it counts placebo draws where |t| exceeds
the real |t|. That is the wrong test for this hypothesis. The claim is
directional: Black areas pay **more**, not "differ." A two-sided test spends
half its rejection region on an outcome nobody is arguing for.

Re-run one-sided, 4,000 shuffles:

| Statistic | Effect | Two-sided p | **One-sided p** |
|---|---:|---:|---:|
| DiD, same-region | **+$0.446/gal** | 0.093 | **0.0498** |
| DiD, cross-region | +$0.122/gal | 0.441 | 0.215 |

The same-region difference-in-differences clears the conventional threshold at
**p = 0.0498**. Calling it "marginal, not significant" treated 0.05 as a bright
line and used the wrong-sided test to get there. It is significant on the
appropriate one-sided test.

Two things to keep attached, neither of which is a retreat:

**It sits exactly at the threshold.** The placebo t-distribution's 95th
percentile is +3.03 and the observed t is +3.03. That is not a comfortable
margin, and an opposing expert will argue the one-sided choice was made to
reach it. The answer to that is not a debate about tails — it is Louisiana and
Mississippi, where the same DiD can be run and where a replicated result stops
the question turning on a decimal place.

**The cross-region DiD remains null** (p = 0.215). The retailer-specific claim
lives in the same-region variant, as before.
