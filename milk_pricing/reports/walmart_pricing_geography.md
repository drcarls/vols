# How Walmart sets milk prices: the pricing unit, recovered

**Date:** 2026-08-22 · Branch `claude/walmart-milk-pricing-sc-m7zc99`
**Question:** "can we find out how walmart sets milk prices by zone? I remember it wasn't by county; it was by region"

**Bottom line:** Your recollection is documented and correct for the regime the literature
covers, and it is still visibly true in a large minority of states — but it is no longer the
whole picture. In our 4,149-store 2026 data the pricing unit is, on average, **at or below
the county**, not a broad multi-county region. That matters because it settles the
bad-control question left open in `tx_ca_metros.md`, and the answer goes against Finding B:
under the one geography where both racial tails actually coexist, Finding B is gone in
every state.

---

## 1. The documented regime: zone pricing, and it is regional

DellaVigna & Gentzkow, *Uniform Pricing in U.S. Retail Chains*, QJE 134(4) 2019 — the
standard reference, built on Nielsen scanner data covering 2006–2014:

> "Six chains vary prices across large regions, but charge nearly uniform prices within
> regions, in a pattern that we call **zone pricing**. […] **The four drugstore chains and
> five mass-merchandise chains in our sample generally practice zone pricing too.**"

Walmart sits in the mass-merchandise category. Their zones are explicitly *supra-county*
and often supra-state — their worked example is that "stores in Georgia and Kentucky share
the same pricing patterns, with little to no difference in prices across stores in these
states," while Illinois and most of Indiana differ. Their operational unit throughout the
paper is the **chain × state**; standard errors are clustered on `parent_code × state`.

Two findings from that paper bear directly on a disparate-impact theory:

- **"Once one controls for pricing zones, pricing is completely rigid within a chain."**
  Within a zone, price does not move with local demographics.
- Prices *do* respond to income — but **between** zones, not within. The within-chain
  income response is "statistically significant, but extremely flat," and they flag this as
  "a puzzle within the puzzle," partly an artifact of sale-price averaging.

So in the documented regime, any demographic gradient in Walmart prices is necessarily a
*between-zone* phenomenon. A within-zone test has nothing to find by construction.

## 2. But the regime has changed

Walmart began deploying digital shelf labels in 2024 and has said they will be in **every
U.S. store by the end of 2026**. Prices can be changed centrally and near-instantly rather
than by re-printing paper tags. The friction that made coarse zones economical — the
managerial and labour cost of a price change — is largely gone. Our data is 2026, not 2014,
and it is markedly finer-grained than the paper's regime. Both things can be true: it was
regional, and it is becoming granular.

## 3. What our own 4,149 stores show

One store = one price (no store in the file quotes two prices), so ZIP-level and store-level
analysis coincide. 184 distinct prices nationally; the top five price points cover only 17%
of stores.

### Zone pricing is unmistakable — in some states

| State | Stores | Distinct prices | Largest single-price block |
|---|---|---|---|
| **VA** | 117 | **2** | 116 stores at $3.64, spanning **63 counties** |
| **NJ** | 59 | **1** | all 59, 19 counties |
| **ME** | 22 | **1** | all 22, 12 counties |
| **ND** | 14 | **1** | all 14 |
| **PA** | 135 | **7** | 39 stores, 13 counties |
| **UT** | 47 | 3 | 42 stores (89%), 13 counties |
| **CO** | 79 | 5 | 65 stores (82%), 20 counties |
| **CA** | 252 | 14 | 71 stores, 16 counties |
| **LA** | 100 | 10 | 35 stores, 18 counties |
| — | | | |
| TX | 421 | **52** | 50 stores |
| NC | 167 | 41 | 29 stores |
| GA | 160 | 39 | 32 stores |
| AL | 117 | 34 | 22 stores |

**Watch out for a confound in that top group.** USDA lists Maine, Montana, Nevada, New York,
North Dakota, Pennsylvania and Virginia as operating state classified-pricing programs, and
the Pennsylvania Milk Marketing Board sets **minimum retail** milk prices by milk marketing
area — PA has **6** such areas and we observe **7** price points across 135 stores. ME (1
price), ND (1), MT (3 across 15), NV (5 across 39, 64% on one point) and VA (2 across 117)
all show the same compression. In those states the flat price is at least partly *regulation*,
not Walmart's zone policy. New Jersey is not on the USDA list, so its single statewide price
does look like a genuine Walmart zone.

### Nationally, though, the unit is at or below the county

Store-level ln(price), national:

| Partition | Groups | R² | adj. R² |
|---|---|---|---|
| ZIP2 prefix | 98 | 57.2% | 56.2% |
| State | 51 | 53.5% | 52.9% |
| **ZIP3 region** (sectional centre) | 808 | 78.8% | 73.6% |
| **County** | 1,727 | **90.8%** | **84.3%** |

Nested, which is the test that does not reward extra groups symmetrically:

- County adds **57.8%** of the residual variance on top of state × ZIP3.
- ZIP3 adds only **11.6%** on top of county.

And the direct measure: within a multi-store **county** the price range is a median of
**$0.04**, and 43.5% of such counties have one identical price. Within a multi-store **ZIP3
region** the range is a median of **$0.19**, and only 31.6% are uniform. The median recovered
price block is 2 stores spanning 2 counties, and **57% of multi-store counties are split
across two or more price blocks**.

So: real zones exist and some are enormous, but the modal pricing unit today is county-sized
or smaller. Not a region.

### Walmart is not simply passing through the federal differential

Regressing store price on the county's Class I differential ($/cwt; 11.63 gal/cwt):

- **No fixed effects:** −0.0247 $/gal per $1/cwt (t −3.26) → pass-through **−0.29×**. Negative.
- **Within state:** +0.0319 (t +1.49) → **0.37×**, not significant.

The Class I zone explains 20.8% of national price variance on its own and adds 26.6% of the
residual within state. There is a cost signal, but Walmart's retail price is not a marked-up
differential, and the two theories are not mechanically the same thing.

## 4. What this does to Finding B — the decisive result

The open question from `tx_ca_metros.md` was whether county fixed effects are a *bad control*
that absorbs the mechanism. The pricing-unit evidence says county FE is roughly the right
granularity nationally, but it has a separate, fatal problem for this design: **counties
almost never contain both racial tails** (1–4 of 25–39 per state). So county FE has nothing
to compare.

The ZIP3 region fixes that. It is exogenous (postal geography, not defined by price), it is
multi-county, it is a plausible proxy for a pricing region — and, critically, **the tails do
coexist inside it**:

- **SC rural:** high-Black stores span ZIP3s 291–299, low-Black span 290, 295, 296, 297, 299 —
  **4 shared regions**. Four of the eight low-Black price points are also occupied by
  high-Black stores.
- **LA rural:** high-Black spans 11 ZIP3s, low-Black spans 4 — **all 4 shared**. All three
  low-Black price points are also occupied by high-Black stores. The $0.106 raw gap comes
  entirely from high-Black stores additionally occupying five higher price points
  ($4.64/$4.66/$4.72/$4.73/$4.74) that no low-Black store occupies.

Rural Walmart whole-milk price on %Black, income and log(pop) controlled:

| State | n | No FE | **ZIP3-region FE** | County FE |
|---|---|---|---|---|
| SC | 59 | +0.00164 (t +0.33) | **−0.00868 (t −1.56)** | −0.00034 (t −0.04) |
| LA | 71 | **+0.00418 (t +2.72)** | **+0.00028 (t +0.37)** | −0.00140 (t −1.71) |
| MS | 61 | +0.00001 (t +0.01) | +0.00174 (t +0.53) | −0.00188 (t −0.64) |
| AR | 76 | +0.00550 (t +1.93) | −0.00498 (t −1.40) | −0.01620 (t −2.33) |
| NC | 122 | −0.00608 (t −1.89) | −0.01069 (t −1.85) | −0.00359 (t −0.54) |
| AL | 91 | −0.00469 (t −1.66) | −0.00056 (t −0.16) | −0.00172 (t −0.41) |
| GA | 95 | −0.00022 (t −0.08) | −0.00575 (t −1.62) | −0.00259 (t −0.38) |
| TN | 89 | +0.00792 (t +1.44) | **−0.02404 (t −3.08)** | −0.01354 (t −0.81) |
| TX | 207 | −0.00787 (t −2.75) | −0.00938 (t −3.29) | −0.01182 (t −3.23) |

With SEs clustered on the region and a **within-region permutation test** on %Black:

- **LA** (12 regions): +0.00028, cluster t +0.43, permutation one-sided **p = 0.30**. Gone.
- **SC** (10 regions): −0.00868, cluster t −1.13, permutation one-sided **p = 0.996**
  (two-sided p = 0.0087 — significantly *negative*). Reversed.

**Not one state is positive under region fixed effects.**

### The one exception, and why it does not rescue the finding

Using the **USDA Class I zone** as the region instead — the coarsest sub-state partition
tested, 3–7 zones per state — Louisiana not only survives but strengthens: **+0.00483
(t +3.51)**. SC goes to −0.00288 (t −0.49), AR to +0.00161 (t +0.49), TX to −0.00932 (t −3.27).

So the state of play is: Finding B's %Black coefficient in Louisiana is **+0.0042 with no
region control, +0.0048 under Class I zones, +0.0003 under ZIP3 regions, and −0.0014 under
counties.** It survives under exactly one of the four geographies, and that is the one with
the fewest groups. That is a specification-dependent result, not a robust one, and an
opposing expert will run all four.

## 5. What to do with this

1. **Stop describing Finding B as a store-level pricing effect.** The evidence says Walmart's
   milk price is set for a block of stores, and the racial gradient lives entirely
   *between* blocks. That is still a cognizable disparate-impact theory — a facially neutral
   zone-assignment practice with a racially disparate distribution — but it is a different
   theory from "Walmart charges Black shoppers more," and it needs to be pleaded as the
   former.
2. **The discovery ask is now specific.** Not "how do you price milk," but: *produce the price
   zone / price group assignment for every store, the definition and boundaries of each zone,
   the criteria by which stores are assigned, and the history of reassignments.* If a store's
   zone assignment is the decision, that assignment is the challenged practice, and it is a
   discrete, documented, produced artifact. DellaVigna–Gentzkow is the citation establishing
   that mass-merchandise chains have such zones.
3. **Ask separately when Walmart's granularity changed.** The digital-shelf-label rollout
   (2024 → all stores by end 2026) is the plausible break point. Pre- and post-rollout price
   files would show whether the pricing unit got finer, which is both a merits fact and a
   class-definition fact.
4. **Finding A is unaffected** and remains the stronger theory. The Class I differential is a
   published federal schedule keyed to county; there is no zone-assignment ambiguity to
   litigate, and Walmart's weak, statistically insignificant 0.37× within-state pass-through
   confirms the two findings are not the same effect counted twice.
5. **Do not lead with the state-level compression table.** VA, PA, ME, ND, MT and NV are
   confounded with state milk price regulation and an opposing expert will say so first.

## Sources

- Stefano DellaVigna & Matthew Gentzkow, "Uniform Pricing in U.S. Retail Chains,"
  *Quarterly Journal of Economics* 134(4), 2019 —
  https://academic.oup.com/qje/article-abstract/134/4/2011/5523148 ·
  working paper: https://www.nber.org/papers/w23996
- USDA AMS, "States with Classified Pricing Programs" —
  https://www.ams.usda.gov/rules-regulations/moa/dairy/classified-milk-pricing
- Pennsylvania Milk Marketing Board, minimum producer and resale prices —
  https://www.pa.gov/agencies/pmb/minimum-prices
- CNBC, "Walmart digital price labels are coming to every store shelf in U.S. by end of 2026"
  (Mar 2026) — https://www.cnbc.com/2026/03/21/walmart-digital-price-tags-will-be-in-every-us-store-by-end-of-2026.html
- Walmart corporate, "Digital shelf labels are a win for customers and associates" (Jun 2024) —
  https://corporate.walmart.com/news/2024/06/06/new-tech-better-outcomes-digital-shelf-labels-are-a-win-for-customers-and-associates

## Reproduction

`analysis/pricing_unit.py` — every table in §3 and §4.
Input: `data/national_walmart_official.csv` (4,149 stores; gitignored).
