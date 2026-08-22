# Re-testing the memo's Walmart-only finding, with no Aldi involved

You were right that my retraction over-reached. Your Finding B never used Aldi, so a defect in my Aldi collection cannot touch it. Re-run on its own terms — the full 4,150-store national file, Walmart prices only, your matching design, with permutation inference — here is what it shows.

## Your design does survive correct inference, in four states

| State | pool | pairs | Cross-region gap | t | **Permutation p** |
|---|---:|---:|---:|---:|---:|
| **LA** | 6 | 33 | +$0.276 | 7.23 | **0.0050** |
| **MS** | 4 | 36 | +$0.928 | 6.06 | **0.0143** |
| **SC** | 10 | 25 | +$0.356 | 3.63 | **0.0167** |
| **AR** | 43 | 15 | +$0.180 | 1.86 | **0.0367** |
| NC | 48 | 26 | −$0.466 | −4.73 | 1.0000 |
| AL | 29 | 24 | −$0.330 | −2.12 | 0.9367 |
| GA, TN, TX, FL | — | — | ≈0 | — | n.s. |

Permutation p-values, not nominal t — the correction I insisted on. **SC clears at 0.017 and LA at 0.005.** My earlier statement that there is no measured retail race effect in any state was wrong, and I withdraw it. Two states also run significantly *negative*, as your memo already discloses.

## But the pooled framework does not corroborate SC and LA specifically

Same file, rural tail sample (1,923 ZIPs, 38 states), state fixed effects, SEs clustered on state. Testing your **pre-specified** states — chosen before any of my work, so not circular:

| Interaction | coef | t |
|---|---:|---:|
| BlackZIP × **SC/LA/VA** (your three "robust" states) | −0.0006 | **−0.01** |
| BlackZIP × **SC/LA** | +0.0322 | **0.33** |
| BlackZIP × SC/LA/**AR** | +0.2269 | 1.88 |
| BlackZIP × SC/LA/MS/**AR** *(post-hoc)* | +0.2541 | **2.31** |

The pooled interaction only reaches significance once **AR and MS** are included — the two states your memo *excluded*, one dismissed as a federal-layer story and one recorded with the opposite sign. Your headline pair, SC and LA, is indistinguishable from the national average in this framework.

## Reconciling the two

Both results are real and they answer different questions.

- **The matched design asks:** within this state, do majority-Black rural ZIPs pay more than income-and-population-matched majority-white ones? For SC and LA the answer is yes, and it survives permutation.
- **The pooled regression asks:** is the Black-ZIP effect in SC and LA *different from* the effect in the other 36 states? The answer is no — but the national average is itself near zero, and with 35 SC tail ZIPs out of 1,923 that interaction has little power. A null interaction is not a null effect.

So the defensible reading is **not** that SC and LA are refuted. It is that they are established within-state and not shown to be exceptional between-state.

## What I would put in the memo now

1. **Keep SC and LA, and report permutation p-values** (SC 0.017, LA 0.005) rather than nominal t. They survive the strongest objection I could make.
2. **Reinstate Arkansas.** It is significant (p=0.037) with the largest comparator pool of any state (43), and it is one of the two states carrying the pooled interaction. The federal-gradient reason for dropping it is testable and should be tested rather than assumed.
3. **Correct Mississippi's sign.** It is +$0.93 at the ≤10% threshold your other states use, not −$0.31 at ≤20%. It is also load-bearing for the pooled result.
4. **Drop Virginia.** Its gaps are identically zero in this file.
5. **Keep NC and AL as disclosed negatives** — they are significant in the other direction and disclosing them is what makes the positives credible.
6. **State the pooled-interaction result yourself.** SC and LA are not distinguishable from the national average. Better from you than from an opposing expert.

## What my Aldi work is still good for

Nothing, until it is rebuilt. The $2.19 fallback contaminates every thin-footprint state. But note it never touched your analysis — and the two states where Aldi data is clean (SC and GA, zero fallback ZIPs) are exactly where a rebuilt control retailer comparison would be valid.
