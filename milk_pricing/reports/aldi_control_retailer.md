# Aldi as a control retailer for the SC retail-premium finding

Running the memo's exact design on Aldi, over the same ZIPs, same demographics, same rural/urban split, same matching. Aldi is a useful control because it is a different chain selling the same product in the same places: anything geographic should move both, anything Walmart-specific should not.

Coverage: 23 of the 25 majority-Black rural SC ZIPs and 10 of 10 white rural comparators carry an Aldi price. Walmart is re-run on the same 23 so the comparison is exact.

## Result

| Design | Walmart | Aldi | Difference-in-differences |
|---|---:|---:|---:|
| Cross-region (n=23) | +$0.339 (t=3.19) | **+$0.217 (t=2.77)** | +$0.122 (t=1.26) |
| Same-region (n=16) | +$0.421 (t=2.81) | **−$0.025 (t=−0.28)** | **+$0.446 (t=3.03)** |

Two things fall out, and they cut in opposite directions.

## 1. Aldi validates the same-region control

This is the strongest support the memo's method has. Aldi shows a **large and significant cross-region gap of its own (+$0.217, t=2.77)** — and that gap **disappears entirely under the same-region control (−$0.025)**, while Walmart's persists and grows.

That is exactly what a valid control should do. The same-region restriction is supposed to strip out the federal-floor/geography component; on Aldi it strips the whole thing. It behaves as a placebo and returns a clean null. The difference-in-differences — Walmart's gap minus Aldi's, which nets out anything geographic moving both chains — is **+$0.446 (t=3.03)**.

For counsel this is a direct answer to the obvious defense ("this is geography, not pricing"): a second chain in the same ZIPs at the same federal floor shows no gap.

## 2. Aldi also weakens the cross-region headline

The other side. **Aldi reproduces about 64% of Walmart's cross-region gap** (+$0.217 against +$0.339). Whatever the cross-region design is picking up, most of it is not Walmart-specific — it is common to any grocer operating across the same SC geography, and the cross-region DiD is only +$0.122 (t=1.26, not significant).

So the headline +$0.48 cross-region figure should not be read as a Walmart retail premium. On this evidence roughly two-thirds of it is regional. **The Walmart-specific claim lives entirely in the same-region variant** — which is the variant resting on two distinct comparators (17 of 18 pairs on one ZIP, per the previous reconciliation).

## 3. The matching-free version does not reach significance

The cleanest possible form of the question needs no matching and no comparator pool at all — within each ZIP, take Walmart's price minus Aldi's, then compare that spread between Black and white rural ZIPs:

| | Walmart − Aldi spread |
|---|---:|
| Black rural ZIPs (n=23) | +$0.355 |
| White rural ZIPs (n=10) | +$0.193 |
| Difference | **+$0.162 (Welch t=0.85)** |

Right sign, right order of magnitude, **not significant**. Walmart does price further above Aldi in Black rural ZIPs, by about 16 cents, but with ten white rural ZIPs the sample cannot establish it without the matching design.

## What I would tell counsel

1. **Add Aldi as a control retailer to the memo.** It is a stronger placebo for the geography defense than the staples basket, because it holds the product fixed and varies the chain. The same-region DiD of +$0.446 (t=3.03) is a better headline than the raw +$0.48.
2. **Stop citing the cross-region figure as a retail premium.** Aldi shows two-thirds of it. Expect this to be found.
3. **The same-region result now carries more weight and more risk.** It is where the Walmart-specific claim lives, and it is the variant with two comparators and $17.7k of income mismatch. That combination should be resolved before filing, not after.
4. **The binding constraint is still ten white rural SC ZIPs.** Both the comparator concentration and the insignificant matching-free DiD trace to it. Pooling Louisiana — the memo's other robust state — would test whether the same Aldi pattern holds there.

## Caveats on my side

- Aldi prices come from its Instacart-powered delivery storefront, which returns a serving zone's price for any ZIP, including rural ZIPs with no reachable store. It is a posted price, not necessarily a locally-available shelf price.
- Aldi and Walmart prices were collected at different times, so a common time trend is not differenced out.
- Aldi's benchmark is Friendly Farms whole gallon against Walmart's Great Value: both private-label whole milk, but not an identical product.
