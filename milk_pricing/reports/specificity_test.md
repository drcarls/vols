# Testing the specificity argument

Your argument: the effect appearing in SC/LA but *not* at Aldi in the same ZIPs and *not* at Walmart elsewhere is evidence it is real, because a confound would show up everywhere.

**The principle is sound.** Specificity with a null control is exactly what distinguishes a mechanism from a confound, and it is why the Aldi comparison was worth building. The problem is that specificity strengthens an effect that exists; it cannot establish one. So I tested SC/LA in the form you mean it — a tail contrast, not a continuous gradient, since diluting a tail effect across the full range was the mistake you caught me making before.

## Six specifications

| Specification | Coef | t |
|---|---:|---:|
| Continuous %Black, all rural ZIPs | +0.0034 | 0.85 |
| Continuous × SC/LA/MS | +0.0021 | 0.21 |
| **Black-ZIP indicator (≥30% vs ≤10%), tail sample** | **+0.0903** | **0.61** |
| Tail × SC/LA/MS | −0.0053 | −0.02 |
| **Tail × SC/LA only (your hypothesis)** | **−0.1652** | **−0.85** |
| Tail, income & population as quintile dummies | +0.0261 | 0.20 |
| **Tail × SC/LA, nonparametric controls** | **−0.2058** | **−1.16** |

All null. The SC/LA interaction is **negative** in both forms that test it directly. The nonparametric version was the steelman — matching handles nonlinear income confounding that a linear control misses, so I replaced the linear terms with income and population quintile dummies. It made no difference.

## The number that decides it

Raw Walmart-minus-Aldi spread, by state, no modelling at all:

| State | Black ZIPs (≥30%) | White ZIPs (≤10%) | **Raw difference** |
|---|---:|---:|---:|
| SC | +$0.424 (n=25) | +$0.193 (n=10) | **+$0.231** |
| **LA** | **+$1.262 (n=33)** | **+$1.242 (n=6)** | **+$0.020** |
| MS | +$1.372 (n=36) | +$0.705 (n=4) | **+$0.667** |

**Louisiana's raw gap is two cents.** The matched design reported +$0.276 with t=5.52 for LA — the largest t-statistic of any state. That entire result is the matching, not the data. LA is the weakest of the three states on the raw numbers while being the strongest on the matched ones, and that inversion is the clearest evidence that the design was generating the finding.

## What the state levels actually show

Look down the middle two columns rather than across. The Walmart-over-Aldi spread is **+$0.19–0.42 in South Carolina and +$1.24–1.26 in Louisiana** — for Black *and* white ZIPs alike. Walmart's premium over Aldi is a large, real, **state-level** phenomenon that varies by more than a dollar between states and barely at all by race within them.

That is a genuine finding and it is not the one the memo makes.

## Where something might still be

**Mississippi** is the only state with a raw difference of any size (+$0.667). It also has the worst support: **four** white rural comparator ZIPs. And MS is the state where the memo reports the opposite sign (−$0.31) from what both the national file and my collection show (+$0.86 to +$0.93). Before anything is built on Mississippi, that contradiction needs resolving — it is currently the only place the retail claim has anywhere to stand, and the two sources disagree about its direction.

## What I would say to counsel

The specificity argument is the right argument and the Aldi control is worth keeping. But it needs an effect to be specific *about*, and across six specifications on 631 tail ZIPs in 11 states there is not one. The retail claim rests on a matching design that inverts Louisiana's raw two-cent gap into its most significant result.

Finding A does not have this problem. Its coefficient barely moves under controls (t=29 raw, t=25 controlled), it needs no matching, and it rests on a published federal rule. That is where the case is.
