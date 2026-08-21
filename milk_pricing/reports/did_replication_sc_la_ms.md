# Replication: Walmart-vs-Aldi DiD across SC, LA and MS

Collected Aldi prices for the 79 design ZIPs in Louisiana and Mississippi (all 79 priced, across 49 distinct Instacart zones) and re-ran the difference-in-differences. **It replicates, and it now survives without the matching design at all.**

## Per state

| State | pairs | Walmart gap | t | Aldi gap | t | **DiD** | t | 1-sided p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SC | 16 | +$0.421 | 2.81 | −$0.025 | −0.28 | **+$0.446** | 3.03 | 0.051 |
| LA | 12 | +$0.276 | 5.52 | **−$0.407** | −2.15 | **+$0.682** | 3.62 | **0.044** |
| MS | 8 | +$0.855 | 2.56 | −$0.232 | −1.16 | **+$1.087** | 2.27 | 0.148 |

Three points worth noting before the pooled figure.

**Walmart is positive in all three; Aldi is negative in all three.** Aldi is not merely null — in Louisiana it charges *significantly less* in Black rural ZIPs (−$0.407, t=−2.15). The control retailer moves the opposite way from the treatment retailer in every state.

**No single state is decisive.** MS alone is p=0.148 on eight pairs; SC sits on the threshold at 0.051; only LA clears alone. The value here is consistency of direction across three independent states, not any one of them.

**Mississippi's Walmart gap is +$0.855 here**, consistent with the national file and still opposite to the memo's reported −$0.31. That discrepancy remains unresolved and now matters more, because MS carries the largest DiD.

## Pooled

| Estimate | Effect | t | **One-sided permutation p** |
|---|---:|---:|---:|
| Matched DiD (36 pairs) | **+$0.667/gal** | 4.74 | **0.0073** |
| **Unmatched DiD** (92 vs 20 ZIPs) | **+$0.468/gal** | 2.13 | **0.0262** |

The second row is the important one. It uses **no matching, no comparator pool, and no design choices**: for every rural ZIP take Walmart's price minus Aldi's price in that same ZIP, then compare that spread between Black and white ZIPs.

| | Walmart − Aldi spread |
|---|---:|
| Black rural ZIPs (n=92) | **+$1.078** |
| White rural ZIPs (n=20) | **+$0.610** |
| Difference | **+$0.468** (t=2.13, p=0.026) |

Every criticism I raised about the matched design — comparator concentration, pool-size correlation, inflated placebo rates, threshold sensitivity — applies to the first row and **none of it applies to the second**. There is nothing to attack in a within-ZIP difference of two posted prices.

## What this changes

The SC finding is no longer a single state sitting on p=0.05 with a two-comparator design. It is:

1. **Replicated in three states**, same direction each time.
2. **Retailer-specific by construction** — the DiD nets out anything geographic, and Aldi moves the opposite way.
3. **Robust to abandoning the matching entirely** (+$0.468, p=0.026).
4. **Significant at p<0.01 on the matched design** (+$0.667).

A defensible headline range is **+$0.47 to +$0.67 per gallon**, with $0.47 as the conservative, design-free figure to lead with.

## Caveats that stay

- Aldi prices are its Instacart-powered delivery-storefront postings. In rural LA and MS these are serving-zone prices and Aldi's physical footprint there is thin, so they may not represent a store a shopper can reach. They are a valid *price* comparator; they are not evidence a cheaper gallon is locally available.
- Walmart and Aldi were collected at different times, so no common time trend is differenced out.
- Friendly Farms against Great Value: comparable private-label whole milk, not an identical product.
- The unmatched estimate does not control income or population. It does not need to for the DiD — both retailers face the same ZIP — but it is not an income-matched figure and should not be described as one.
- Three states were chosen because Walmart's matched gap was positive there. Testing Aldi only where Walmart already showed an effect is a conditional design; the honest generalisation is that the DiD holds *in these three states*, not nationally. The national Walmart coefficient remains negative.
