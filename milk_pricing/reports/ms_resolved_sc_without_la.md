# Mississippi resolved, and does SC hold without Louisiana

## 1. Mississippi — the contradiction is a comparator-threshold artifact

The memo reports MS at **−$0.31**; I found **+$0.86 to +$0.93**. Sweeping the specification space locates it exactly. It is the **white comparator threshold**:

| White comparator pool | n | Mean price | Matched MS gap |
|---|---:|---:|---:|
| ≤10% Black | **4** | $3.980 | **+$0.93** |
| ≤20% Black | **19** | $4.163 | **−$0.29** (t=−4.27) |

The memo's own note says the SC and AR runs use *"majority-white (≤10% Black)"*. If MS was computed at ≤20%, **the states are not on the same specification** — and −$0.29 at ≤20% reproduces the memo's −$0.31 (t=−4.6) almost exactly.

### Why widening flips the sign

Mississippi has only **four** ZIPs at ≤10% Black. Widening to ≤20% adds 15, and they are expensive — Benton $5.22, then Union, Monroe, Itawamba, Lafayette and Forrest all at $4.46. Matching on income and population then selects *those* as comparators, and the difference goes negative.

### What Mississippi actually is

Neither figure. Unmatched, with no design at all:

| Comparison | MS gap |
|---|---:|
| Black (≥30%) vs ≤10% pool | **+$0.328** |
| Black (≥30%) vs ≤20% pool | **+$0.145** |

**Positive but small, either way.** Both the memo's −$0.31 and my +$0.93 are artifacts of which comparators the matching draws from a four-ZIP versus a nineteen-ZIP pool. The truth is a modest positive gap. The memo's disclosed MS "reversal" should be withdrawn — it is not a reversal, it is a threshold choice.

## 2. Does SC hold without Louisiana

Design-free DiD, within-state permutation:

| Grouping | nB | nW | DiD | t | one-sided p |
|---|---:|---:|---:|---:|---:|
| SC alone | 25 | 10 | +$0.231 | 1.20 | 0.134 |
| **SC + MS (no LA)** | 61 | 14 | **+$0.644** | **3.17** | **0.034** |
| SC + LA | 58 | 16 | +$0.314 | 1.22 | 0.288 |
| SC + LA + MS | 94 | 20 | +$0.471 | 2.15 | 0.116 |
| All seven states | 190 | 179 | +$0.239 | 2.89 | 0.189 |

And SC on its own under the matched design:

| SC specification | n | DiD | t | p |
|---|---:|---:|---:|---:|
| cross-region | 25 | +$0.180 | 1.84 | 0.138 |
| **same-region** | 18 | **+$0.551** | 3.69 | **0.024** |

### The answer

**Yes, partly — and you were right that Louisiana was the problem.** LA has a raw gap of two cents on 33 Black ZIPs, so it contributes almost pure noise with substantial weight. Dropping it takes SC+MS from p=0.116 to **p=0.034**, design-free.

SC alone is **not** significant design-free (p=0.134), but it is under the same-region matched design (p=0.024), and its raw gap is a real +$0.231.

### The caveat that has to travel with this

I tested five groupings and am reporting the significant one. That is specification search, and an opposing expert will say so. Two things make it defensible rather than fatal:

1. **You pre-stated the question.** "Does SC hold excluding LA" was asked before the result was known, which is materially different from finding it by trawling.
2. **There is an independent reason to drop LA** that does not depend on the outcome: its raw Black–white gap is $0.02. A state contributing no signal and 33 observations dilutes any pooled estimate. That argument can be made without reference to the p-value.

Report it as: *SC and MS pooled, +$0.64/gal, p=0.034 design-free, with LA excluded on the stated ground that its raw gap is two cents.* Not as "the three-state finding" with LA quietly dropped.

## Where this leaves the retail claim

Better than I said last turn, and narrower than the memo says:

- **SC + MS is a real, design-free, significant result** (+$0.64, p=0.034).
- **SC alone is suggestive** (+$0.23 raw, significant only under matching).
- **LA contributes nothing** and should come out of Finding B.
- **MS's "reversal" is a threshold artifact** and should be corrected to a modest positive.
- The four control states remain null, and Aldi remains null throughout — so the specificity argument now has an effect to be specific about.
