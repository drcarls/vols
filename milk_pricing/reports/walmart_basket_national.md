# Walmart: fluid milk is the only item that varies by store

**Date:** 2026-08-24 · Branch `claude/walmart-milk-pricing-sc-m7zc99`
**Collected:** Bright Data "Walmart – products" dataset, 442 requests, 247 store×item observations

**Bottom line:** Confirmed on Walmart, not just Aldi. Across ~20 randomly drawn stores per item,
**Great Value whole milk takes 17 distinct prices, 1% milk 17, chocolate milk 19.** Every other
item in the basket takes **one or two**. Mozzarella, sour cream and canned green beans are a
single price nationwide. Whole milk runs **$2.72 in Chicago to $5.17 in Brentwood PA**.

The sharpest form of it: two stores that happened to draw the full basket — **Sacramento CA and
Ashburn VA, 2,800 miles apart — price 8 of 13 items identically to the cent**, and differ on
milk.

---

## 1. What was collected, and the South Carolina caveat up front

**This is a national random sample, not South Carolina.** Store pinning could not be made to
work on this Bright Data account. Three mechanisms were tested and all three failed:

| Attempt | Result |
|---|---|
| Web Unlocker `/request` with `zip` (and `state`) | empty response — not a valid field for this zone |
| URL params `?storeId=`, `?athstid=`, `?location=` | ignored; successive requests resolved to Sacramento, Nashville, Ashburn |
| Store cookies `locGuestData`, `ASSORTMENT_STORE_ID` | ignored; still Sacramento |
| Dataset API with a `zipcode` input field | silently dropped by the **`Walmart - products`** scraper; identical inputs gave Sacramento twice and Saginaw once |

> **Correction (same day).** That last row reflects the wrong scraper. The account also holds
> **`Walmart - products zipcodes`** (`gd_m693oc1r1gebnayxq`), which takes a **`zip_code`** field and
> *does* resolve a real local store. It still cannot be used here: the price it returns is
> Walmart's national online price, flat across the country and below Pennsylvania's legal minimum.
> See `reports/brightdata_zipcode_trap.md`. The collection below is unaffected — its prices are
> the realistic ones.

The account holds one zone (`unblocker`, no geo targeting), so the serving store is set by the
scraper's exit IP. **This is the same defect that produced the bad sample earlier in this
project** — and it is now characterised rather than merely suspected.

What the dataset *does* return is the store it actually hit (`store_id`, `store_location`).
Repeating a URL with a distinct cache-busting parameter (`?cb=N`) defeats the dataset's URL
deduplication and draws a fresh random store. That gives a random national sample of real,
identified stores — sufficient for a dispersion comparison **across products**, which is the
question, but not for an SC analysis. The draw happened to include three SC stores (Rock Hill,
Wallace, Greenwood); nowhere near enough to analyse.

Every SKU was verified by its returned `product_name` — all 13 match the intended item.

## 2. The result

Dispersion across distinct stores, one observation per store×item:

| Item | Tier | Stores | Mean | CV | **Distinct prices** | Range |
|---|---|---|---|---|---|---|
| **whole milk** | fluid milk | 19 | $3.69 | **19.0%** | **17** | $2.72–$5.17 |
| **1% milk** | fluid milk | 20 | $3.26 | **15.7%** | **17** | $2.16–$4.15 |
| **chocolate milk** | fluid milk | 22 | $3.68 | **14.0%** | **19** | $2.82–$4.62 |
| vegetable oil 48 oz | pantry | 20 | $3.86 | 4.7% | 5 | $3.52–$4.18 |
| white bread 20 oz | traffic driver | 17 | $1.47 | 3.4% | 2 | $1.27–$1.48 |
| large eggs 12 ct | butter/eggs | 20 | $1.66 | 3.0% | 2 | $1.44–$1.67 |
| all-purpose flour 5 lb | pantry | 20 | $2.40 | 2.5% | 2 | $2.38–$2.58 |
| Greek yogurt 32 oz | other dairy | 23 | $2.98 | 2.1% | 2 | $2.97–$3.28 |
| butter sticks 16 oz | butter/eggs | 20 | $3.00 | 1.2% | 2 | $2.98–$3.06 |
| cottage cheese 24 oz | other dairy | 18 | $2.88 | 1.0% | 2 | $2.87–$3.00 |
| **shredded mozzarella** | other dairy | 16 | $1.97 | **0.0%** | **1** | — |
| **sour cream 16 oz** | other dairy | 16 | $1.84 | **0.0%** | **1** | — |
| **canned green beans** | pantry | 16 | $0.82 | **0.0%** | **1** | — |

By tier:

| Tier | Items | Mean CV | Median distinct prices |
|---|---|---|---|
| **Fluid milk** | 3 | **16.2%** | **17** |
| Traffic driver (bread) | 1 | 3.4% | 2 |
| Butter & eggs | 2 | 2.1% | 2 |
| Other dairy | 4 | 0.8% | 2 |
| Pantry | 3 | 2.4% | 2 |

Fluid milk takes a different price at essentially **every store sampled**. Nothing else takes
more than five, and three items take exactly one across the country.

## 3. The within-store version

Two stores drew all 13 items. Sacramento CA and Ashburn VA:

| Item | Ashburn VA | Sacramento CA | diff |
|---|---|---|---|
| cottage cheese | 2.87 | 2.87 | **0.00** |
| eggs 12 ct | 1.67 | 1.67 | **0.00** |
| flour 5 lb | 2.38 | 2.38 | **0.00** |
| Greek yogurt | 2.97 | 2.97 | **0.00** |
| green beans | 0.82 | 0.82 | **0.00** |
| mozzarella | 1.97 | 1.97 | **0.00** |
| sour cream | 1.84 | 1.84 | **0.00** |
| white bread | 1.48 | 1.48 | **0.00** |
| whole milk | 3.46 | 3.52 | −0.06 |
| butter sticks | 2.98 | 3.06 | −0.08 |
| chocolate milk | 3.52 | 3.63 | −0.11 |
| vegetable oil | 3.97 | 4.18 | −0.21 |
| **1% milk** | 3.09 | 3.46 | **−0.37** |

**Eight of thirteen identical to the cent** across the width of the country. The items that move
are the three milks, plus butter and oil by small amounts.

## 4. Where this differs from Aldi — and it matters

`reports/dairy_pattern.md` found a three-tier structure at Aldi: fluid milk variable, butter and
eggs at two price points, everything else one statewide price. **Walmart's carve-out is
narrower.** Butter (1.2%) and eggs (3.0%) sit with the flat items, not in a middle tier.

So at Walmart the exception is **fluid milk alone** — not "traffic drivers" as a class. That is
a materially better fact for the case than the Aldi pattern suggested:

- A defence that Walmart simply "prices traffic drivers competitively" does not fit. Bread and
  eggs are traffic drivers by any definition and they are flat.
- The practice is therefore specific to one category, which makes it a discrete, identifiable
  decision rather than a general pricing philosophy.

## 5. Corroborating detail

The four highest whole-milk prices are **Brentwood PA $5.17, Meadville PA $4.94, Brownsville PA
$4.94, Bowmansdale PA $4.63** — all Pennsylvania, which is the state whose Milk Marketing Board
sets **minimum retail** milk prices (`reports/walmart_pricing_geography.md` §3). An independent
pull, collected blind, reproduces the regulatory structure found in the national file. That is a
useful validation of both datasets.

## 6. What this does and does not do for the case

**Does:**
- Establishes on the defendant's own shelves that fluid milk is priced by store while adjacent
  private-label goods are priced nationally. The client's recollection is confirmed, and
  narrowed usefully: milk alone, not traffic drivers generally.
- Kills the "we price all our KVIs locally" defence in advance.
- Confirms a **mechanism capable of** producing geographic disparity in milk and only milk.

**Does not:**
- **Say anything about race.** This is a dispersion result. It is a necessary predicate for the
  disparate-impact theory, not evidence of it.
- **Cover South Carolina.** The sample is national and store selection was not controllable.
- **Support a within-store placebo regression yet.** That needs the same basket at the same
  ~4,149 stores as the milk file, which requires store pinning this account cannot do.

## 7. What is needed next

The full test in `analysis/basket_test.py` §5 — milk relative to the flat basket, regressed on
%Black across thousands of pinned stores — is now the only remaining step, and the single
blocker is **store pinning**. Options:

1. **The client's own collection method**, which produced 4,149 correctly pinned stores. Adding
   these 13 SKUs to that pull is the shortest path and the SKUs are now known (see the script).
2. **A geo-targeted Bright Data zone** — residential or ISP with `country-state-city` targeting
   in the proxy username. This account has only `unblocker`, so this needs a new zone.

## Reproduction

`analysis/walmart_basket_national.py` · data `data/walmart_basket_national.csv` (gitignored).
SKUs used are listed in the script; all were resolved by search and verified against the
returned `product_name`.
