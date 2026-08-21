# Not stronger — reorganised. And the case is Arkansas, not South Carolina

I should have run the pooled-interaction test before presenting SC+MS as a clean result last turn. Running it changes the answer.

## SC+MS does not survive the pooled framework

| Interaction (tail sample, 631 ZIPs, 11 states, state FE, clustered SE) | coef | t |
|---|---:|---:|
| BlackZIP × **SC/MS** | +0.1327 | **0.54** |
| BlackZIP × **SC alone** | **−0.0619** | **−0.36** |
| BlackZIP × **MS alone** | **+0.4770** | **2.78** |
| BlackZIP × LA alone | −0.2742 | −1.66 |

The SC+MS result I reported at p=0.034 is **entirely MS**. South Carolina on its own is not significant design-free (p=0.130) and is *negative* in the pooled interaction. The memo's lead state is the weakest part of its own claim.

## Every state, ranked by raw design-free DiD

| State | nB | nW | Raw DiD | t | permutation p |
|---|---:|---:|---:|---:|---:|
| **AR** | 15 | **42** | **+$1.009** | **4.05** | **0.0002** |
| MS | 36 | **4** | +$0.667 | 1.36 | 0.109 |
| TN | 6 | 63 | +$0.322 | 0.79 | 0.212 |
| SC | 25 | 10 | +$0.231 | 1.20 | 0.130 |
| LA | 33 | 6 | +$0.020 | 0.04 | — |
| GA | 40 | 19 | +$0.007 | 0.03 | — |
| NC | 26 | 48 | −$0.026 | −0.17 | — |
| AL | 24 | 29 | −$0.044 | −0.24 | — |
| TX | 9 | 97 | −$0.335 | −1.35 | — |

**Arkansas is the strongest state in the dataset by a wide margin, and it has the best support.** Forty-two white rural comparators against MS's four and SC's ten. With nine states tested, Bonferroni requires p<0.0056; **AR clears it at 0.0002. SC and MS do not clear it at all.**

## What Arkansas actually shows

| | Black rural ZIPs | White rural ZIPs | Difference | t |
|---|---:|---:|---:|---:|
| Walmart | $4.397 | $3.963 | **+$0.434** | **4.65** |
| Aldi | $2.962 | $3.537 | **−$0.575** | **−2.28** |
| **Spread** | $1.435 | $0.426 | **+$1.009** | **4.05** |

Both halves are significant and they move in opposite directions. Walmart charges $0.43 more in Black rural Arkansas; Aldi charges $0.58 **less**. This is the only state where the Walmart gap stands on its own without the Aldi control doing the work.

## The memo discarded Arkansas for a reason the Aldi control answers

The memo says AR's premium *"does not survive the same-region control (its apparent gap was largely the Delta-vs-Ozark federal gradient)"* and calls AR *"a federal-layer story."*

That reasoning does not apply to a retailer difference-in-differences. Aldi faces the same Delta-vs-Ozark federal gradient in the same ZIPs, so differencing it out removes exactly the confound the memo was worried about. The gradient cannot explain a gap that survives subtracting another chain's prices in the same places — and AR's does, at +$1.009 with p=0.0002.

**Arkansas was discarded using a control that the Aldi comparison supersedes.**

## The answer to "stronger than before"

No. What changed is the identity of the finding:

| | Before | Now |
|---|---|---|
| Lead state | SC (+$0.48, t=3.6) | **AR (+$1.01, p=0.0002)** |
| SC status | the case | **not significant (p=0.130)** |
| MS status | disclosed reversal | modest positive, thin (4 comparators) |
| LA status | robust (+$0.26) | **contributes nothing ($0.02 raw)** |
| AR status | dismissed as federal-layer | **the strongest result in the data** |

The retail claim is no stronger than two turns ago. It is in a different state than the memo says, resting on better support than the memo's states have, and it survives a multiple-comparisons correction that nothing else does.

## What I would do next

1. **Rebuild Finding B around Arkansas.** It is the only state that survives correction, has a real comparator pool, and shows a significant Walmart gap independent of the control retailer.
2. **Demote SC and LA out of the retail finding.** SC p=0.130, LA raw gap $0.02. Neither is defensible as a headline.
3. **Correct the MS reversal** to a modest positive, per the threshold analysis.
4. **Check whether AR's Aldi discount is real or an artifact of Aldi's thin Arkansas footprint.** A −$0.58 Aldi gap is large and deserves the same scrutiny I have been applying to Walmart's.
