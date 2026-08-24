# The full Great Value basket across all 92 South Carolina Walmart stores

**Date:** 2026-08-24 · Branch `claude/walmart-milk-pricing-sc-m7zc99`
**Collected:** Bright Data "Walmart - products zipcodes", 1,196 requests → **1,191 records**,
13 items × 92 SC stores, resolving by `zip_code` alone

**Two findings, one of which is genuinely new:**

1. **The milk carve-out is present even in Walmart's online price book.** Whole milk takes **25
   distinct prices** across 92 SC stores; sour cream, mozzarella, Greek yogurt, eggs and canned
   green beans each take **exactly one**. The three-tier structure found at Aldi and in the
   national Walmart sample reproduces here.
2. **No item with real price variation shows a racial gradient.** The three fluid milks — the
   only items with meaningful dispersion — are null: whole milk t = −0.22, 1% t = −0.17,
   chocolate t = −0.56.

**Caveat, unchanged and load-bearing:** 1,188 of 1,191 records are labelled `"Price when
purchased online"`. Against the known SC shelf prices this series correlates **r = +0.065** with
**1 of 92 exact matches**. This is Walmart's *online* price in South Carolina, not the shelf
price. See `reports/brightdata_zipcode_trap.md`.

---

## 1. Dispersion by item

| Item | Tier | n | Mean | CV | **Distinct prices** | Modal share | Range |
|---|---|---|---|---|---|---|---|
| **whole milk** | fluid milk | 92 | $3.54 | **11.7%** | **25** | 72% | $1.97–$5.31 |
| **chocolate milk** | fluid milk | 92 | $3.57 | **9.1%** | **22** | 71% | $2.74–$5.13 |
| **1% milk** | fluid milk | 92 | $3.41 | **7.4%** | **19** | 71% | $2.37–$3.92 |
| vegetable oil | pantry | 91 | $4.08 | 4.2% | 5 | 71% | $3.52–$4.18 |
| white bread | traffic driver | 92 | $1.47 | 2.3% | 3 | 92% | $1.36–$1.62 |
| butter sticks | butter/eggs | 91 | $3.04 | 1.0% | 2 | 80% | $2.98–$3.06 |
| flour 5 lb | pantry | 92 | $2.38 | 0.9% | 3 | 97% | $2.34–$2.58 |
| cottage cheese | other dairy | 91 | $2.87 | 0.6% | 2 | 97% | $2.78–$2.87 |
| **eggs 12 ct** | butter/eggs | 91 | $1.67 | **0.0%** | **1** | 100% | — |
| **Greek yogurt** | other dairy | 92 | $2.97 | **0.0%** | **1** | 100% | — |
| **canned green beans** | pantry | 92 | $0.82 | **0.0%** | **1** | 100% | — |
| **sour cream** | other dairy | 92 | $1.84 | **0.0%** | **1** | 100% | — |
| **mozzarella** | other dairy | 91 | $1.97 | **0.0%** | **1** | 100% | — |

By tier:

| Tier | Items | Mean CV | Median distinct prices |
|---|---|---|---|
| **Fluid milk** | 3 | **9.4%** | **22** |
| Traffic driver (bread) | 1 | 2.3% | 3 |
| Pantry | 3 | 1.7% | 3 |
| Butter & eggs | 2 | 0.5% | 2 |
| Other dairy | 4 | **0.1%** | **1** |

Five of thirteen items are a single price from Spartanburg to Hilton Head. Whole milk takes 25.
This is the third independent reproduction of the pattern — Aldi's SC panel, the national
Walmart sample, and now Walmart's SC online book.

## 2. The racial gradients — and four rows that must not be read

%Black on price, income controlled:

| Item | Distinct prices | Coefficient | |
|---|---|---|---|
| **whole milk** | 25 | **−0.00072 (t −0.22)** | null |
| **chocolate milk** | 22 | **−0.00143 (t −0.56)** | null |
| **1% milk** | 19 | **−0.00034 (t −0.17)** | null |
| vegetable oil | 5 | −0.00369 (t −2.87) | significant, **negative** |
| white bread | 3 | −0.00014 (t −0.51) | null |
| flour 5 lb | 3 | +0.00004 (t +0.26) | null |
| butter sticks | 2 | −0.00050 (t −2.04) | significant, **negative**, sd $0.03 |
| cottage cheese | 2 | +0.00008 (t +0.66) | null |
| sour cream | **1** | +0.00000 (t +3.24) | **DEGENERATE — ignore** |
| Greek yogurt | **1** | +0.00000 (t +1.91) | **DEGENERATE — ignore** |
| green beans | **1** | −0.00000 (t −1.65) | **DEGENERATE — ignore** |
| mozzarella | **1** | +0.00000 (t +1.34) | **DEGENERATE — ignore** |
| eggs 12 ct | **1** | +0.00000 (t +1.41) | **DEGENERATE — ignore** |

**Sour cream's t = +3.24 is not a finding.** Sour cream is $1.84 at all 92 stores. With zero
variance in the outcome there is nothing to explain; the coefficient is zero to five decimals
and the t-statistic is floating-point noise in the pseudo-inverse. The same applies to Greek
yogurt, green beans, mozzarella and eggs. `analysis/sc_basket.py` now labels these DEGENERATE
rather than printing a bare t-statistic — anyone scanning the column for stars would otherwise
"find" a racial disparity in sour cream pricing.

**Among items that can be tested, every result is null or negative.** The three fluid milks —
the only ones with substantial dispersion, and the ones the theory is about — are flat on race.

## 3. Sanity check against the clean series

| | |
|---|---|
| Correlation, this series vs. known SC shelf price (whole milk, n=92) | **r = +0.065** |
| Exact matches | **1 / 92** |
| Known shelf price on %Black, same 92 stores | +0.00338 (**t +0.81**) — null |

The two series are effectively uncorrelated, which confirms the online/shelf distinction rather
than undermining it. And on the question that matters they agree: **null.**

## 4. What to take from this

- **For the memo's retail theory: nothing changes.** SC shows no racial gradient in Walmart milk
  pricing, on either the online series (t = −0.22) or the shelf series (t = +0.81), consistent
  with `why_sc_varies.md`, `within_metro_test.md` and `zone_vs_override.md`.
- **The milk carve-out is now very well established** — three independent datasets, two
  retailers, two price books. Walmart and Aldi both manage fluid milk store-by-store while
  pricing adjacent dairy nationally. That is a documented mechanism, and it is the strongest
  survivable fact from the retail side.
- **It is still not a disparity.** A mechanism capable of producing geographic price differences
  is a predicate for the theory, not evidence for it, and every test of the racial step has come
  back null.
- **Where the online book is interesting on its own:** Walmart varies milk online by store
  25 ways in one state while charging one national price for sour cream. If the case ever needs
  to show that milk is treated as a deliberate exception, this dataset shows it cleanly and was
  collected in a way anyone can reproduce.

## Reproduction

`analysis/sc_basket.py` (`--build` converts the raw snapshot) · data `data/sc_basket.csv`
(gitignored, 1,191 rows with both price series and demographics per store).
Snapshot `sd_mt75cwttarjb46cn8`.
