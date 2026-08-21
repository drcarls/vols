# Pooled regression: the retail finding does not survive

You were right to ask why more states were worth collecting, and the pooled regression you asked for is what settles it. It settles it against Finding B.

## The specification

All rural ZIPs where both retailers are priced: **937 ZIPs across 11 states** (TX 163, NC 121, GA 94, AL 91, TN 89, AR 74, LA 71, NY 63, MS 61, SC 59, CA 51). State fixed effects, standard errors clustered on state.

This is a strictly better test than the matched design. It uses every rural ZIP rather than only the ≥30% / ≤10% tails, needs no comparator pool, has no threshold to tune, and handles the state clustering that inflated the earlier t-statistics.

## Result

| Outcome | % Black coef | t | |
|---|---:|---:|---|
| Walmart price | −0.00038 | −0.25 | null |
| Aldi price | −0.00383 | −1.09 | null |
| **Spread (Walmart − Aldi)** | **+0.00344** | **0.85** | **null** |

What *is* significant is income (Walmart −0.0078, t=−5.44) and market size (Walmart −0.0103, t=−4.25; spread −0.0125, t=−3.26). Price tracks how poor and how small a market is. It does not track race.

The spread coefficient implies that a 40-point rise in Black share is associated with about **14 cents** more Walmart-over-Aldi spread, with a t-statistic of 0.85. Not distinguishable from zero.

## And it is not state-specific either

The natural defense is that the effect lives only in SC, LA and MS. Tested directly, with an interaction:

| Term | coef | t |
|---|---:|---:|
| % Black | +0.00280 | 0.65 |
| **% Black × (SC/LA/MS)** | **+0.00209** | **0.21** |

On Walmart price alone the interaction is +0.00024 (t=0.11). **The three test states are not statistically distinguishable from the other eight.**

## Why this disagrees with the matched design

The matched design returned +$0.45 to +$1.09 in those three states. The regression sees nothing. The difference is not the data — it is the same ZIPs. It is what each method uses:

| | Matched design | Pooled regression |
|---|---|---|
| ZIPs used | tails only (≥30% / ≤10%) | all 937 |
| Comparators | 4–10 white rural per state | every ZIP |
| Reuse | with replacement | none |
| Threshold | tunable | none |
| Clustering | ignored | state FE + clustered SE |

When a finding appears under a design that discards most of the sample and reuses a handful of controls, and vanishes under one that uses everything, the regression is the more credible of the two.

## What this means for the memo

**Finding B, as currently framed, is not supported.** The retail premium is an artifact of the matching specification. Specifically:

1. The pooled race coefficient on the spread is null (t=0.85).
2. The SC/LA/MS interaction is null (t=0.21).
3. The national Walmart-only coefficient with state FE was already negative (−0.0017, t=−3.45) on all 4,140 stores.
4. Aldi is null throughout, so this is not a control-retailer problem.

Three independent specifications now point the same way. I would not put Finding B in front of counsel in its current form.

## What survives, and it is not nothing

- **Walmart's rural premium is real and large** — market size drives price (t=−4.25), and rural low-population markets pay materially more. That is a documented, defensible disparity.
- **It falls disproportionately on Black and poor communities** because those communities are disproportionately in small rural markets. That is a disparate *outcome*, cleanly measurable, and it does not require a race coefficient to state.
- **Finding A (the federal differential) is untouched by this.** It is a different mechanism with a much larger sample and, per the memo, t-statistics in the dozens. Nothing here bears on it.
- **Georgia's disjoint federal floors** (Black rural 5.8–6.0/cwt, white rural 5.4–5.6, 2 of 39 with a same-floor comparator) independently corroborate the memo's Black Belt argument.

The honest reframing is that the retail layer shows a **size-and-income gradient with disparate racial incidence**, not race-based retail pricing. That is a weaker claim than Finding B makes, and it is one the data actually supports.
