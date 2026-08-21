# Reconciliation: my SC null vs the memo's +$0.45 retail premium

**The memo is right and my earlier conclusion was wrong.** I reproduced the SC finding from your 92-store file. One caveat on the same-region variant is worth attaching before it goes to counsel.

## The reproduction

| | Memo | My run on your file |
|---|---|---|
| Majority-Black rural SC ZIPs | 25 | **25** |
| White comparator pool | ~10 | **10** |
| Cross-region gap | +$0.48 (t=4.9, n=25) | **+$0.356 (t=3.63, n=25)** |
| Same-region gap | +$0.45 (t=3.6, n=19) | **+$0.479 (t=3.45, n=18)** |

Same counts, same direction, same order of magnitude. The differences are tie-breaking and implementation detail, not substance.

## Why I missed it

My analysis was mis-specified for this question in four ways, all mine:

1. **I fit a continuous `%Black` term across all 92 stores.** The effect is a tail contrast — heavily Black rural against heavily white rural — and a linear term across the full range dilutes it toward zero.
2. **My 'white' comparators were ≤20–25% Black; the memo uses ≤10%.** I was comparing Black areas to moderately-Black areas and calling the result a null.
3. **I did not restrict both sides to rural.** Mixing urban in imports the urban/rural price step as noise.
4. **I matched mostly without replacement.** With only ten white rural ZIPs available, that discards most of the treated group.

My within-zone argument was also answering the wrong question. Showing that a price zone contains both 5% and 56% Black ZIPs at one price rules out *within-zone* differentiation. It says nothing about whether Black areas are disproportionately **assigned** to expensive zones — which is the actual claim, and which is true.

## Matching-free corroboration

The zone-assignment claim holds without any matching at all:

| Rural SC ZIPs | n | Median $/gal | Share in ≥$3.70 zones |
|---|---:|---:|---:|
| ≥30% Black | 25 | **$3.82** | **60%** (15/25) |
| 10–30% Black | 24 | $2.87 | 33% (8/24) |
| ≤10% Black | 10 | $3.12 | 30% (3/10) |

Majority-Black rural ZIPs are twice as likely to sit in Walmart's most expensive SC zones. That is the finding, and it needs no matching design to see.

## The caveat counsel should have

In my reproduction the same-region test — the one the memo calls decisive — **rests on a single comparator**:

| Comparator ZIP | Pairs using it |
|---|---:|
| 29576 (Georgetown, $2.88) | **17 of 18** |
| 29630 (Anderson, $3.26) | 1 |

Dropping 29576 leaves one pair. The 18 differences are not 18 independent comparisons; they are 17 Black ZIPs measured against one white ZIP, so the paired t-statistic of 3.45 has roughly **1 effective degree of freedom**, not 17. The memo already discloses that matching with replacement "modestly inflates retail t-stats" — in the SC same-region case the inflation is not modest.

Income matching also degrades badly under the same-region constraint: mean mismatch rises from **$7,017** (cross-region) to **$17,724** (same-region), median $19,738, max $34,417. Most of those 17 pairs compare a $31k–$50k Black ZIP to a $65,890 white one — so the same-region test buys federal-floor comparability by giving up much of the income matching that made the design credible.

The conservative bound, with no matching at all: rural Black mean $3.449 vs rural white $3.171, **+$0.278, Welch t = 1.39** — the right direction, not significant at n=10 on the white side.

## What I would put in front of counsel

1. **The directional finding is sound** and survives a matching-free test (60% vs 30% in the top zones). Lead with that; it has no design to attack.
2. **Report the same-region result with comparator-clustered inference**, or state plainly that it rests on one control ZIP. Opposing counsel will find this, and finding it first is much cheaper.
3. **The income mismatch under the same-region constraint needs disclosing** alongside the $8k figure already in the memo — it is $17.7k in that variant.
4. **The binding constraint is the white rural comparator pool: ten ZIPs.** South Carolina may simply not contain enough majority-white rural ZIPs at the same federal floor to support a clean same-region test — the same structural point the memo already makes for Georgia and Mississippi.

None of this touches Finding A, the federal differential analysis, which I have not attempted to reproduce.
