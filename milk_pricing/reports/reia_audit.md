# USDA's own economic analysis: $4 billion, and no analysis of who pays it

**Date:** 2026-09-12 · Branch `claude/walmart-milk-pricing-sc-m7zc99`
**Document:** *Regulatory Economic Impact Analysis of the Recommended Decision to Amend Federal
Milk Marketing Order Pricing Formulas*, USDA/AMS, July 2024 — AMS-DA-23-0031-0003. **Eight
pages.**

**Bottom line: this changes where the case lives.** The spine is no longer a statistical
gradient in a cost surface. It is a four-document chain in the agency's own record, in which
USDA quantified a **$4.01 billion** revenue transfer, expressly declined to run its own
econometric model *because* the county-level Class I differentials made it too complex, was told
on the record that the cost would land on WIC and SNAP participants, and then certified no civil
rights impact in three sentences.

---

## 1. The chain

| # | Document | Date | Fact |
|---|---|---|---|
| 1 | **REIA** (8 pp.) | Jul 2024 | Quantifies the transfer: **Class I revenue +$4.01bn**, pool value **+$2,366,951,414.39** over 2019–2023 |
| 2 | **REIA §I** | Jul 2024 | **Declines to run the dynamic econometric model**, because the Class I differential changes required revisions across **3,108 counties** |
| 3 | **MIG exceptions** (55 pp.) | Sep 2024 | *"The consumers bearing this price increase include women, school children, WIC, and SNAP participants"* |
| 4 | **Final rule** (53 pp.) | Jan 2025 | CRIA is **three sentences**; *"No major civil rights impact is likely"*; the word **"consumer" appears zero times** |

Each link is a quotation from a public document. None of it depends on my regressions.

## 2. USDA quantified the benefit precisely

Class I revenue under the amendments, 2019–2023 (Table 3):

| FMMO | Original | Recommended | Increase |
|---|---|---|---|
| Northeast | $7.60bn | $8.48bn | **+$874.1M** |
| Mideast | $5.66bn | $6.41bn | +$747.4M |
| **Appalachian** | $3.63bn | $4.10bn | **+$470.1M** |
| Central | $3.93bn | $4.34bn | +$410.4M |
| **Southeast** | $2.91bn | $3.24bn | **+$328.9M** |
| California | $4.42bn | $4.72bn | +$302.6M |
| Southwest | $3.78bn | $4.05bn | +$276.2M |
| Upper Midwest | $1.97bn | $2.20bn | +$225.6M |
| **Florida** | $2.21bn | $2.41bn | **+$204.9M** |
| Pacific Northwest | $1.45bn | $1.56bn | +$111.2M |
| Arizona | $1.19bn | $1.24bn | +$58.2M |
| **Total** | **$38.76bn** | **$42.77bn** | **+$4.01bn** |

USDA's own words: *"The total Class I revenue with the recommended amendments is calculated to be
$42.7 billion across all FMMOs; an increase of $4 billion."* And: *"The value, however, increases
$2.3 billion over the 5-year period analyzed."*

**The three Southeastern orders — Appalachian, Southeast, Florida — account for $1.00bn, 25% of
the national increase.** In the sampled store-ZIPs, Southern-order states hold **51% of the
population but 75% of the Black population**. That is the bridge between the record and the
incidence finding, and it is the right way round: the record establishes the transfer, the
demographics establish where it lands.

## 3. USDA declined to model the impact — and said why

Verbatim, §I:

> **"The dynamic AMS regional econometric model was not used due to the complexity of the changes
> trying to be incorporated.** In order to use the dynamic model, all of the price formula changes
> must be incorporated, including the Class I differential changes. Previous to this rulemaking,
> the dynamic model had 11 Class I pricing points to conduct impact analyses for proceedings which
> did not address Class I differential changes. However, since this recommended decision is
> proposing to change the Class I differentials, **the model required revisions to incorporate the
> current and proposed differentials in each of the 3,108 counties in the contiguous 48 States.**
> These additional changes significantly enhanced the complexity of an already complex econometric
> model. Since the model attempts to reflect future behavior regarding changes in milk pooled by
> order and resulting impacts, each change must be run independently, and **the imposed statutory
> time constraints contained in 7 CFR 900.28 made it impossible to complete."**

Read that closely. **The reason USDA did not model the impacts is the very feature that creates
the geographic incidence** — differentials set county by county across 3,108 counties. The agency
substituted a static Excel recalculation whose stated premise is: *"Beyond the proposed pricing
formula changes, all other variables remain unchanged."*

## 4. Neither analysis considers who pays

Across the REIA's 8 pages and 17,263 characters:

| Term | Occurrences |
|---|---|
| consumer, retail, household, school | **0** |
| WIC, SNAP, nutrition | **0** |
| low-income | **0** |
| incidence, distributional | **0** |
| public, benefit | **0** |
| producer | 7 |
| handler / processor | 1 / 1 |

Combined with the final rule (0 of 590,370 characters mentioning consumers), **neither the
economic analysis nor the civil rights analysis for a $4 billion increase in the minimum price of
drinking milk contains a single word about the people who buy it.**

## 5. The qualification, and it is mine

**$4.01bn at the pool level is not $4.01bn of consumer burden, and my own work is the reason to
say so.** Pass-through of the Class I differential into Walmart's shelf price, measured on 4,128
stores, is **0.37× within state (t = 1.68, not significant)** and *negative* unconditionally
(`reports/walmart_pricing_geography.md` §3). Fluid milk is also priced store-by-store in ways
only loosely coupled to the federal floor (`reports/dairy_pattern.md`).

So the honest formulation is: **USDA moved $4.01bn and performed no analysis of the incidence —
and the incidence is genuinely uncertain, including by my estimates.** That is the
failure-to-consider argument, not a damages figure. Anyone who presents $4bn as consumer harm
will be met with my own pass-through number.

## 6. What this does to the strategy

**Before:** a 13.5¢/gal racial gradient in a federal cost surface, robust to income (t 7.50),
but 95% between-state and not significant within state (t 1.83) — an incidence statistic whose
legal significance was unclear.

**Now:** an administrative-record argument with the statistic as support rather than as the
claim. The elements, in the order a reviewer would meet them:

1. USDA quantified a $4.01bn transfer to producers (its own Table 3).
2. It declined to model the impacts, citing the county-level differentials and §900.28 timing.
3. A represented party objected that the cost would fall on WIC and SNAP participants and lower-income consumers.
4. The final rule certified no impact on low- and moderate-income populations in three sentences, never using the word "consumer."
5. Independent analysis shows the differential is $1.57/cwt higher in ZIPs ≥30% Black than ≤10% — 13.5¢/gal, robust to income.

Element 5 is now doing the job it is actually fit for: showing the unexamined incidence was not
random. It is no longer carrying the claim.

**The *Block* problem is unchanged.** *Block v. Community Nutrition Institute*, 467 U.S. 340
(1984) confines judicial review of milk marketing orders to handlers. Everything above makes the
merits stronger without making an NAACP-brought suit more available. The realistic vehicles remain
a handler petition under 7 U.S.C. § 608c(15)(A), an administrative civil-rights complaint to USDA
OASCR, a rulemaking petition, or the next amendment cycle.

## 7. Still unaudited

- The **49-day hearing transcript**. USDA's justification for deviating from the USDSS model
  lives there, and so does whatever anyone said about consumers in testimony.
- The memo's **§6 alternative-schedule counterfactual** — the less-discriminatory-alternative
  element. MIG's objection that USDA *"deviat[ed] from the USDSS model"* and used current
  differentials *"as a floor"* is adjacent to it and was raised by a party with standing. **This is
  now the single highest-value remaining task.**
- Whether a **completed CRIA worksheet** exists behind the three-sentence certification. FOIA.

## Reproduction

`analysis/reia_audit.py`. The REIA is public at
`https://downloads.regulations.gov/AMS-DA-23-0031-0003/content.pdf` — retrieval requires a
browser User-Agent, a Referer header and `?api_key=`, or the host returns 403.
