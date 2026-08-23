# Is there a pattern across dairy products? Yes — a three-tier one

**Date:** 2026-08-22 · Branch `claude/walmart-milk-pricing-sc-m7zc99`
**Question:** the other dairy products already pulled — is there a pattern there?

**Bottom line:** There is, and it is stark. In `data/aldi_sc_observations.json` — 25 products
at each of 20 South Carolina Aldi stores, pulled in one pass — **fluid milk carries 10–14
different prices across the state while 13 of 20 other products carry exactly one.** Cottage
cheese is $3.15 in Hilton Head and $3.15 in Spartanburg. Greek yogurt is $2.79 everywhere.
Shredded mozzarella $3.29 everywhere. Whole milk runs $2.39 to $3.58 a gallon.

This is the comparison-basket test, already collected — on **Aldi**, not Walmart. That is a
real limitation (§4), but it is corroboration from an independent retailer that fluid milk is
on a different pricing regime from everything around it.

---

## 1. Two corrections applied first

- **Size.** Whole Milk and 2% Milk each mix 0.5 gal and 1 gal rows. On raw price they show a
  CV of 29%; **normalized to $/gal that falls to 14–16%.** Roughly half the apparent dispersion
  was a size artifact. All figures below are size-normalized ($/gal for fluid, $/oz for solids).
- **The file's own `category` field is unreliable** — it labels vegetable oil sticks, eggs,
  cottage cheese and mozzarella as `dairy_white`. Tiers below are assigned explicitly in
  `analysis/dairy_pattern.py`, not read from the data.

## 2. The pattern

| Tier | Products | Mean CV | One price across all of SC |
|---|---|---|---|
| **Fluid milk** | 3 | **14.1%** | **0 of 3** |
| Butter & eggs | 4 | 4.5% | 0 of 4 |
| Other dairy & grocery | 13 | **0.0%** | **13 of 13** |

Product by product:

| Product | CV | Distinct prices across 20 stores |
|---|---|---|
| Friendly Farms 2% Milk | 15.8% | **14** |
| Friendly Farms Whole Milk | 13.9% | **13** |
| Friendly Farms Low Fat Chocolate Milk | 12.7% | **10** |
| Pure Irish Butter, salted | 8.1% | 2 |
| Large White Eggs, 1 dozen | 3.9% | 2 |
| Salted Butter Sticks | 3.1% | 2 |
| Unsalted Butter Sticks | 3.1% | 2 |
| Cottage cheese · Greek yogurt ×2 · shredded mozzarella · string cheese · liquid egg whites · pasture-raised eggs · free-range eggs · organic eggs · Moo Tubes ×2 · spreadable Irish butter · vegetable oil sticks | **0.0%** | **1** |

The gradient tracks how much of a traffic driver each item is. **Refrigerated fluid milk —
including chocolate milk — is managed store by store. Butter and eggs get two price points.
Everything else gets a single statewide price.**

That chocolate milk moves with white milk (12.7%, 10 prices) is worth noting: the carve-out is
the **refrigerated fluid-milk case**, not white milk specifically. It matches the finding in
`why_sc_varies.md` that all four Walmart fat levels disperse identically and 73% of stores price
them the same.

## 3. Walmart and Aldi move together on milk

Across the 13 ZIPs holding both:

- **correlation r = +0.444**
- **Walmart sits below Aldi in 10 of 13 markets, median spread −$0.13**

| ZIP | Aldi $/gal | Walmart $/gal | spread |
|---|---|---|---|
| 29301 Spartanburg | 2.39 | 2.32 | −0.07 |
| 29607 Greenville | 2.65 | 2.50 | −0.15 |
| 29801 Aiken | 2.75 | 2.67 | −0.08 |
| 29203 Columbia | 2.85 | 2.72 | −0.13 |
| 29501 Florence | 2.95 | 2.82 | −0.13 |
| 29730 Rock Hill | 3.49 | 3.32 | −0.17 |
| 29926 Hilton Head | 3.55 | 3.86 | **+0.31** |
| 29150 Sumter | 2.45 | 3.78 | **+1.33** |
| 29572 Myrtle Beach | 3.58 | 2.88 | **−0.70** |

A tight undercut of roughly a dime in most markets is a competitive-matching signature and
supports the mechanism hypothesised in `why_sc_varies.md` §5. The exceptions are the
interesting cases — **Sumter, where Walmart sits $1.33 above Aldi**, is a 48%-Black market and
the single largest gap in the set. With 13 points that is an anecdote, not a finding, but it is
the shape of thing worth looking for at scale.

## 4. What this does and does not establish

**Does:**
- Fluid milk is priced on a fundamentally different regime from adjacent dairy, at a real
  retailer, in the state at issue. The claim that milk is the exception is not folklore.
- **The design works.** This is a within-store cross-product comparison, and it produces a
  signal so large it needs no statistics: 0.0% versus 14.1% CV. It is the strongest argument
  for running the Walmart basket.
- **The instrument objection does not apply to the comparison.** These are Instacart delivery
  prices and the serving store may not be the nearest store — but that affects all 20 products
  at a given ZIP identically. No instrument artifact produces one price for thirteen products
  and thirteen prices for milk.

**Does not:**
- **This is Aldi.** The client's recollection concerned Walmart's private brand, and Walmart is
  the defendant. Aldi is corroboration, not substitution.
- **20 stores, one state, one pull.** The demographic regression on Aldi milk is n=13 and null
  on everything (%Black −0.0037, t −0.48); it is reported for completeness and should not be
  cited.
- **Dispersion is not disparity.** That milk is store-managed says nothing about whether the
  management is racially patterned. It establishes that there is a mechanism capable of
  producing disparity — which is a necessary predicate, not the case itself.

## 5. What follows

1. **This raises the value of the Walmart basket, not lowers it.** The Aldi panel shows the
   design has enormous power. The same pull on Walmart, at the ~4,149 stores already covered,
   would carry the racial question the Aldi panel is far too small to carry.
2. **Prioritise butter and eggs in that basket.** The Aldi tiering says they are the informative
   middle case — variable, but only across two price points. If Walmart's milk moves and its
   butter does not, the carve-out is narrow and specific; if butter moves too, the practice is
   "traffic drivers," which is broader and easier to justify as ordinary competitive response.
3. **The single-statewide-price items are the ideal placebo.** Cottage cheese, yogurt and
   mozzarella have zero variance to explain, so any racial gradient found on milk at a store
   where those items are flat cannot be a store-level confound. That is exactly the denominator
   `analysis/basket_test.py` §5 is built on.

## Reproduction

`analysis/dairy_pattern.py`. Input: `data/aldi_sc_observations.json`,
`data/sc_walmart_official.csv`, `data/national_walmart_official.csv` (gitignored).
