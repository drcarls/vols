# Is Pennsylvania's minimum milk price racially discriminatory?

**Date:** 2026-08-24 · Branch `claude/walmart-milk-pricing-sc-m7zc99`

**Short answer: not on the evidence here, and the question is largely untestable in this
data — but the way it fails is instructive, and it produces the most important decomposition
in the project.**

Three findings:

1. **Within Pennsylvania there is no racial price gradient.** Price on %Black is +0.0026
   (t 0.47) raw and +0.0015 (t 0.25) with controls. Null.
2. **The test is nearly impossible to run**, because Walmart's Pennsylvania footprint is far
   whiter than Pennsylvania. Median PA Walmart ZIP is **2.6% Black**; exactly **one** of 134 is
   above 30%. The state is roughly 12% Black.
3. **The floor is real and large and regressive** — PA milk runs **$1.74/gal above neighbouring
   states** — but a floor's burden is an *income* story, and nationally the entire milk-burden
   disparity by race comes from the income denominator, not the price numerator.

---

## 1. Within Pennsylvania

The seven regulated price points and who lives at them:

| Price | Stores | Mean %Black | Median income | Urban |
|---|---|---|---|---|
| $3.34 | 2 | 2.9 | $120,933 | 100% |
| $4.65 | 21 | 4.2 | $63,395 | 14% |
| $4.78 | 9 | 3.7 | $84,918 | 67% |
| $4.89 | 19 | 4.5 | $78,625 | 37% |
| $5.17 | 38 | 3.6 | $65,972 | 24% |
| $5.31 | 26 | **8.1** | $93,594 | 77% |
| $5.48 | 19 | 2.1 | $56,748 | 5% |

The highest-%Black tier ($5.31, the Philadelphia suburbs) is also the **highest-income** tier at
$93,594 — and the single most expensive tier ($5.48) is the whitest and poorest. There is no
monotone relationship in either direction.

- Price on %Black: **+0.00264 (t +0.47)** raw; **+0.00154 (t +0.25)** controlling income,
  log(population) and urban.
- Philadelphia 5-county mean $5.23 (8.3% Black) vs rest of PA $5.03 (3.6% Black) — a $0.20 gap
  that tracks metro cost of living, not race, and reverses on income.

## 2. Why the test barely exists

| | |
|---|---|
| PA Walmart ZIPs | 134 |
| Median %Black | **2.6** |
| 90th percentile | 10.6 |
| Maximum | 32.5 |
| ZIPs ≥20% Black | **4** |
| ZIPs ≥30% Black | **1** |

Pennsylvania is about 12% Black, and its Black population is concentrated in Philadelphia and
Pittsburgh — where Walmart Supercenters are scarce. **Walmart's PA footprint is not where Black
Pennsylvanians shop.** Any honest answer about the incidence of PA's floor on Black households
needs a different retailer sample: Philadelphia supermarkets, corner stores and independents,
not Walmart. That is a real study; it is not this data.

## 3. The floor is large and regressive

| State | Stores | Mean $/gal | Distinct prices |
|---|---|---|---|
| **PA** | 134 | **$5.07** | 7 |
| NJ | 58 | $4.43 | 1 |
| WV | 39 | $3.37 | 12 |
| NY | 97 | $3.31 | 29 |
| OH | 141 | $3.04 | 34 |
| MD | 45 | $2.92 | 17 |

**PA premium over its neighbours: +$1.74/gal**, and +$2.15 against Maryland. At 104 gal/year
that is roughly **$181/household/year**, raising milk's share of median household income from
**0.485% to 0.761%**.

A uniform price floor is regressive by construction: it costs every household the same dollars,
so it takes a larger share of a smaller income. That is a genuine equity objection to the PA
statute. It is not, by itself, a racial one.

## 4. The decomposition that matters — and it cuts against the memo

Nationally, across 4,145 stores:

| Outcome | on %Black, raw | + state FE |
|---|---|---|
| **Milk burden** (annual cost ÷ median income) | **+0.00355 pp per point (t +16.15)** | **+0.00286 (t +12.25)** |
| **Milk price** | **−0.00258 (t −3.89)** ⚠ | **−0.00323 (t −6.20)** |
| **Median income** | — | **−$366 per point (t −13.44)** |

> ⚠ **The raw price column does not survive the cleaned panel.** Excluding the eight
> statutorily-regulated and non-contiguous states, the unconditional price-on-%Black coefficient
> falls to −0.00098 (t −1.62) — null. Virginia was the driver: 117 stores at 18.8% mean %Black
> on a statutorily compressed $3.64. The **state-FE** column is unaffected (−0.00374, t −7.09)
> and is the one that matters. See `reports/clean_panel.md` §2.

Read those together. **The milk-affordability disparity by race is enormous and highly
significant — and it is entirely the income denominator.** Blacker communities pay *slightly
less* per gallon (t = −6.2) and earn substantially less (t = −13.4), so milk costs them a much
larger share of income.

This is the cleanest statement of what the retail data supports:

- **A pricing-conduct theory has no support.** Whatever Walmart does store by store, the
  national price gradient by race is negative.
- **An affordability theory is overwhelming** — but it is a finding about income inequality
  expressed through a necessity, not about anyone's pricing conduct. Bread, eggs and rent would
  all produce the same coefficient.

## 5. What this means for the PA question specifically

Putting the pieces together, a disparate-impact claim against the Pennsylvania Milk Marketing
Board would have to be an **incidence** claim: the floor is uniform, uniform costs are
regressive, Black Pennsylvanian households have lower median income, therefore the floor takes
more of their income. The empirics in §3 and §4 support each link.

Four problems that counsel should weigh before anyone builds on it — these are the shape of the
doctrinal difficulty, not a legal opinion:

1. **It proves too much.** Every price floor, flat fee, minimum markup and sales tax on a
   necessity is regressive in exactly this way. A theory that condemns PA's milk floor condemns
   the entire category, which is usually a sign the theory is operating at the wrong level of
   generality for disparate-impact doctrine.
2. **No racial disparity in the price itself**, which is what the statute actually sets. The
   disparity enters only through income, which the statute does not touch.
3. **Different defendant, different regime.** The Board is a state agency, so this is state
   action — equal protection, or Title VI if federal funding attaches — not the retail theory in
   the memo. It would be a separate case against a separate party.
4. **A facially legitimate purpose exists**: dairy farm viability and supply stability. That
   does not end the analysis, but it is the justification any challenge has to overcome, and it
   is not pretextual on its face.

**And note the strategic cost of raising it at all.** Pennsylvania is the strongest counterexample
in this dataset to the memo's core intuition: it has the **highest milk prices in the country**
and an overwhelmingly **white** exposed population, because the cause is regulation, not race.
Introducing PA invites the opposing expert to make exactly that point.

## Reproduction

`analysis/pa_minimum_pricing.py`. Input: `data/national_walmart_official.csv` (gitignored).
Burden figures assume 104 gal/household/year against ZIP median household income; the
coefficient signs and t-statistics do not depend on that constant.
