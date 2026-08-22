# Why South Carolina still has large within-state price variation

**Date:** 2026-08-22 · Branch `claude/walmart-milk-pricing-sc-m7zc99`
**Question:** if ~57 national zones plus overrides is the architecture, why is SC's override sd $0.539 when Louisiana's is $0.195?

**Bottom line:** SC's spread is a **metro discount**. Urban SC stores average $2.82, rural
$3.27 — a **−$0.445** gap that accounts for essentially the whole range. It is not a data
artifact, not the Class I differential, and not a zone boundary: the low band is mixed inside
8 of SC's 10 ZIP3 regions. Urban status predicts it (t +3.04); income and %Black do not
(t −0.13 each). Louisiana is tight because it has no metro discount at all (+$0.085, the wrong
sign). And SC's entire raw racial gap turns out to be composition: Black SC communities are
disproportionately rural and simply don't get the discount.

---

## 1. First, it is real

Two collections, one artifact check each — both clean.

- **The two SC files agree exactly.** All 92 ZIPs present in both `sc_walmart_official.csv`
  and `national_walmart_official.csv` carry identical prices; max |difference| $0.00.
- **It is not a product mismatch.** SC stores quote whole and 2% milk at the *same* price in
  **98%** of the low band and **100%** of the high band. A store at $2.69 prices both fat
  levels at $2.69; a store at $3.69 prices both at $3.69. This is the same private-label
  product at two very different prices, not two different products. (Nationally only 0.6% of
  stores show a whole-vs-2% gap over $0.50; SC's rate is 0.0%.)

The SC distribution is genuinely bimodal: **54 stores from $2.32–$2.97**, **38 from
$3.07–$4.00**, sd $0.539, IQR $1.10. That is a ~35% spread on an identical gallon inside one
state.

## 2. It is not the federal differential

| State | Class I diff ($/cwt) | Mean shelf price | Price sd |
|---|---|---|---|
| **SC** | **$5.86** (highest here) | **$3.11** (lowest here) | $0.539 |
| NC | $5.65 | $3.23 | $0.591 |
| MS | $5.32 | $4.26 | $0.436 |
| **LA** | **$5.12** | **$4.57** | $0.195 |
| VA | $4.81 | $3.64 | $0.028 |
| CA | $2.51 | $3.84 | $0.088 |

SC carries the *highest* Class I differential in this set and the *lowest* shelf price;
Louisiana carries a lower differential and a shelf price $1.46 higher. Consistent with the
−0.29× unconditional pass-through in `walmart_pricing_geography.md`: the federal cost signal is
not what is moving retail.

## 3. It is not a zone boundary

If SC straddled two of the ~57 zones, the low band would be geographically clean. It is not —
only 2 of SC's 10 ZIP3 regions sit entirely on one side of $3.00:

| ZIP3 | Region | Stores below $3.00 |
|---|---|---|
| 292 | Columbia | **6 / 6** |
| 299 | Beaufort / Savannah | **0 / 5** |
| 296 | Greenville | 15 / 19 |
| 298 | Aiken | 4 / 5 |
| 290 | Columbia | 4 / 6 |
| 291 | Columbia | 4 / 7 |
| 293 | Rock Hill | 4 / 7 |
| 294 | Charleston | 7 / 13 |
| 295 | Florence | 8 / 15 |
| 297 | Spartanburg | 2 / 9 |

Mixed inside almost every region. That is the signature of the **store-level override layer**,
not of a zone map. SC is not unusual in this: NC has 37% of its multi-store ZIP3 regions on one
side of the line, OH 50%, IL 44% (TX and AZ are more clustered at 73%).

## 4. It is the metro discount

Modelling P(store is in the low band) in SC:

| Specification | Result |
|---|---|
| income only | +0.0025 (t +0.97) |
| %Black only | −0.0023 (t −0.79) |
| inland ZIP3s only | +0.198 (t +1.93) |
| **urban only** | **+0.313 (t +3.04)** |
| all four together | urban **+0.313 (t +2.84)**; inland +0.193 (t +1.94); income −0.0004 (t −0.13); %Black −0.0005 (t −0.13) |

Urban survives everything. Income and race collapse to nothing once urban is in.

The county table shows it directly — metros at the bottom, rural Pee Dee at the top:

| Low | | High | |
|---|---|---|---|
| Spartanburg | $2.32 | Clarendon | $3.91 |
| Greenville | $2.50 | Dillon | $3.90 |
| Aiken | $2.67 | Chesterfield | $3.82 |
| Richland | $2.73 | Beaufort | $3.76 |
| Lexington | $2.84 | Chester | $3.57 |
| Berkeley | $2.86 | York | $3.38 |
| Horry | $2.90 | Georgetown | $3.37 |

## 5. Why Louisiana is tight

The dispersion **is** the urban–rural gap:

| State | Stores | Price sd | Urban − rural |
|---|---|---|---|
| TN | 120 | $0.724 | **−$0.789** |
| NC | 167 | $0.591 | −$0.616 |
| AL | 117 | $0.579 | −$0.634 |
| **SC** | 92 | $0.539 | **−$0.445** |
| TX | 421 | $0.538 | −$0.532 |
| GA | 160 | $0.502 | −$0.524 |
| MS | 67 | $0.436 | −$0.391 |
| **LA** | 100 | **$0.195** | **+$0.085** |
| CA | 252 | $0.088 | +$0.005 |

Louisiana and California **do not discount their metros** — the gap is flat or slightly
positive — and they are the two tightest states in the set. SC, TN, NC, AL, GA and TX all run a
$0.39–$0.79 metro discount and all have dispersion to match.

**The likely mechanism is competitive adjustment, but this data does not establish it.** The
discretionary competitor adjustments the client describes would produce exactly this pattern —
metros have hard discounters, rural areas do not. Across the 12 states with usable Aldi
coverage, price sd correlates +0.58 with Aldi coverage and the urban–rural gap correlates
−0.54. But n=12, and California breaks it badly (63% Aldi coverage, sd $0.088). My Aldi measure
is Instacart delivery coverage, which reflects a delivery radius rather than store proximity,
so it is the wrong instrument. **Confirming this needs the competitor-adjustment logs**, which
is now a specific discovery item.

## 6. What this does to the SC finding

SC's raw racial gap is composition, not pricing:

| | n | Mean price | Urban share |
|---|---|---|---|
| ZIPs ≥30% Black | 30 | $3.32 | **17%** |
| ZIPs ≤10% Black | 19 | $3.04 | **47%** |
| raw gap | | **+$0.281** | |

Split by geography, the gap reverses inside metros:

- **within urban:** high-Black $2.70 vs low-Black $2.90 → **−$0.204** (Black SC metros are *cheaper*)
- **within rural:** high-Black $3.45 vs low-Black $3.17 → **+$0.278** (this is Finding B's number, t = 0.33, not significant)

So the entire SC disparity is that **Black South Carolinians are disproportionately rural and
therefore disproportionately excluded from the metro discount.**

That is worth thinking about carefully rather than discarding, because it points somewhere the
memo has not gone. The memo restricts to rural ZIPs — which conditions away the single largest
source of racial price disparity in the state. A theory that Walmart's discretionary
competitive discounting systematically bypasses Black communities because of *where* those
communities are is a real disparate-impact structure, it is a $0.28–$0.45 effect rather than
the $0.03 the rural-only design recovers, and it is measured on the layer we now know exists.

It also has a hard problem the memo's version does not: the practice is "discount where a
competitor is present," the disparity runs through rural residence, and Walmart's answer is
that it discounts where it faces competition and Black SC residents happen to live where it
does not. Whether that survives is a legal question about business justification, not a
statistical one. But it is a better-measured claim than the one currently in the memo, and it
should be costed out before the rural-only design is finalised.

## Reproduction

`analysis/sc_variation.py`. Input: `data/national_walmart_official.csv`,
`data/sc_walmart_official.csv`, `data/aldi_pooled.json`, `data/aldi_sc_sweep.json` (gitignored).
