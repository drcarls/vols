# CA and TX: the fallback proven, and what survives in Aldi's real footprint

You were right that Aldi has real footprints in both states, and testing that turned the fallback from a hypothesis into a demonstration.

## The $2.19 rate by county is binary — 0% or 100%

| Texas county | $2.19 rate | | California county | $2.19 rate |
|---|---:|---|---|---:|
| Harris (Houston) | **0 / 35** | | Los Angeles | **0 / 38** |
| Dallas | **0 / 31** | | Riverside | **0 / 24** |
| Collin | **0 / 24** | | San Diego | **0 / 21** |
| Tarrant | **0 / 23** | | San Bernardino | **0 / 14** |
| Denton / Travis / Fort Bend / Brazoria | **0%** | | Fresno / Ventura | **0%** |
| **Bexar (San Antonio)** | **12 / 12 = 100%** | | **Sacramento** | **8 / 8 = 100%** |
| **El Paso** | **6 / 6 = 100%** | | | |

A price that varies by zone does not come out 0% in eleven counties and 100% in three. This maps exactly onto Aldi's actual footprint: dense in DFW and Houston, absent from San Antonio and El Paso; dense in Southern California and the southern Central Valley, absent from Sacramento and the north. **$2.19 is a no-serving-store default, confirmed.**

It also explains the TX urban Hispanic "finding" I reported earlier. El Paso, Laredo and San Antonio are heavily Hispanic *and* outside Aldi's footprint, so they drew the fallback; the low-Hispanic comparators were Collin County, where Aldi is present and prices are real. The confound was perfect.

## Re-tested inside Aldi's real footprint

Restricting to counties with a 0% fallback rate — 147 TX ZIPs across 8 counties, 116 CA ZIPs across 6:

| | nT | nC | Walmart | Aldi | DiD |
|---|---:|---:|---:|---:|---:|
| **TX Hispanic ≥30 vs ≤10** | 61 | **8** | **+$0.220 (t=4.77)** | +$0.095 (t=2.30) | +$0.125 (t=2.35) |
| TX Hispanic ≥50 vs ≤20 | 23 | 46 | +$0.014 (t=0.34) | +$0.078 (t=1.58) | **−$0.065 (t=−1.24)** |
| TX Black ≥30 vs ≤10 | 15 | 66 | −$0.090 (t=−1.91) | −$0.042 | −$0.049 (t=−0.75) |
| CA Hispanic ≥50 vs ≤20 | 55 | 13 | −$0.008 (t=−0.45) | +$0.154 | −$0.162 (t=−0.98) |

### California: nothing

No contrast in California shows anything, and most are untestable — 87 of the 116 clean-county ZIPs are ≥30% Hispanic and **zero** are ≤10%, so there is no comparator group. California Walmart ZIPs are too uniformly Hispanic to support the test at all. The Black contrast is worse: 1 ZIP against 105.

### Texas: one threshold-fragile signal

The Walmart-only Hispanic gap of **+$0.220 (t=4.77)** is real in the clean sample and is close to the memo's reported TX Hispanic +$0.27. But it does not survive a threshold change — at ≥50% vs ≤20% it is +$0.014 (t=0.34) — and its 8 comparators are again affluent Collin County suburbs. Earlier, with county fixed effects, the same contrast went to −0.0003 (t=−0.21).

So: **partial corroboration of the memo's TX Hispanic number at one specification, not robust across specifications.**

## Lidl is not available as a control in either state

Lidl US operates on the East Coast only — Virginia through New York, plus the Carolinas and Georgia. It has **no stores in Texas or California**, so it cannot serve as a second control retailer there. Where it does operate its prices are not published online at all (an identical 109,918-byte page for every product URL), so it contributes footprint only, anywhere.

## What this is actually worth

The valuable output here is not a finding, it is a **validity filter**. The 0%/100% county split gives a clean, mechanical rule for which ZIPs have usable Aldi data:

1. Compute the $2.19 rate per county.
2. Keep only 0% counties.
3. Everything else has no serving store and must be dropped, not imputed.

Applied nationally that leaves SC and GA fully usable, the TX and CA metros usable, and Louisiana, Mississippi, Arkansas and rural Texas largely unusable — which is precisely where my retracted findings came from.
