# Retraction: the Aldi control data contains a fallback price that faked the entire result

Every retail finding I reported using the Walmart-minus-Aldi difference-in-differences is invalid. The cause is a defect in my own Aldi collection.

## The defect

**$2.19 appears in 149 of 1,737 Aldi ZIPs (8.6%)** — the second most common value in the entire dataset, and the floor of every state sweep I ran. It is not a price. It is what the storefront returns for a ZIP with no genuine serving store.

Its distribution gives it away:

| State | ZIPs at $2.19 | Aldi footprint |
|---|---:|---|
| LA | **33.8%** | almost none |
| TX | 18.2% | metro only |
| CA | 16.4% | thin |
| AR | 14.9% | NW corner only |
| MS | 13.1% | almost none |
| **SC** | **0.0%** | dense |
| **GA** | **0.0%** | dense |
| FL | 0.0% | dense |

It appears exactly where Aldi is absent and never where Aldi is dense.

## Why it produced the finding

Within Arkansas the fallback is **differentially distributed by race**:

| AR rural | at $2.19 |
|---|---:|
| Black ZIPs (≥30%) | **7 of 15 = 47%** |
| White ZIPs (≤10%) | **1 of 42 = 2%** |

Remote, poor, disproportionately Black Delta ZIPs are furthest from any Aldi, so they get the fallback. The fallback is low. A low fake Aldi price inflates the Walmart-minus-Aldi spread. The spread inflates precisely where the hypothesis predicted it would.

**This is a selection artifact that mimics the effect it was built to test** — the most dangerous kind, and I did not catch it for many turns despite flagging the underlying risk at the outset.

## Every result, before and after

| Cell | Raw (contaminated) | Cleaned | Verdict |
|---|---:|---:|---|
| **AR rural Black** | **+$1.009 (t=4.05, p=0.0002)** | **+$0.399 (t=1.52, p=0.052)** | **dead** |
| **TX urban Hispanic** | **+$0.512 (t=5.81, p=0.012)** | **+$0.107 (t=1.93)** | **dead** |
| MS rural Black | +$0.667 (t=1.36) | pool collapses to 4 | untestable |
| LA rural Black | +$0.020 | pool collapses to 4 | untestable |
| SC rural Black | +$0.231 (t=1.20) | +$0.231 (t=1.20, p=0.142) | unchanged, null |
| GA / NC / AL / TN / TX rural | null | null | unchanged |

**Not one cell is significant after cleaning.** SC is unaffected because SC has zero fallback ZIPs — which is why it never moved much either way.

## What this invalidates

Everything downstream of the Aldi DiD:

- The Arkansas finding I called "the case" last turn.
- The TX urban Hispanic finding from this turn.
- The SC/LA/MS pooled DiD (+$0.667, p=0.0073) and the SC+MS result (p=0.034).
- The claim that Aldi is a validated null control — its nulls in dense-footprint states were real, but its behaviour in thin-footprint states was noise.
- The argument that the Aldi DiD supersedes the memo's same-region control for Arkansas. It does not; the DiD was broken.

## What is unaffected

Anything that never used Aldi:

- **The national Walmart regression** — race null, income and market size significant, on 4,140 stores.
- **The rural premium** — Walmart's rural-urban step and the population gradient (t=−4.25).
- **The Finding A replication** — Class I differential, raw t=29, t=25 under controls, 93/7 between/within-state.
- **Georgia's disjoint federal floors**, which use no price data at all.
- **The memo's own Walmart-only matched design.** My critique of it — thin comparator pools, inflated t-statistics, the MS threshold artifact — stands, because it was made with Walmart data and permutation tests, not with Aldi.

## What a usable Aldi control would require

1. **Verify each ZIP against Aldi's actual store locator** and drop any with no store within a plausible trade radius. Distance-to-nearest-Aldi should be a recorded field, not an assumption.
2. **Treat repeated identical values as suspect by default.** $2.19 at 8.6% frequency across a supposedly zone-varying price should have been caught the first time I plotted the distribution.
3. **Restrict to dense-footprint states** — SC and GA have zero fallback ZIPs and are the only places this comparison was ever valid.

On the current data the honest position is that **there is no measured retail race effect in any state**, and the apparent ones were mine, not Walmart's.
