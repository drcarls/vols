# The exclusion-cleaned national panel

**Date:** 2026-08-24 · Branch `claude/walmart-milk-pricing-sc-m7zc99`

Excludes **PA, NJ** (minimum retail milk price), **ME, ND, VA, MT** (classified pricing that
reaches retail — all at 0–3% CV), and **AK, HI** (non-contiguous; freight dominates, HI averages
$6.28 on one statewide price). Retains the ~24 states with general below-cost statutes, which
do not bind — see `reports/state_pricing_laws.md`.

**4,145 → 3,768 stores; 51 → 43 states; 377 dropped (9.1%).**

**Bottom line: nothing that matters changes, and two things do.** Finding A is unchanged and
marginally stronger. Finding B is untouched — no test state was excluded. The burden
decomposition is unchanged. But the **raw price-on-race gradient loses its significance**, and
the **zone/override split flips**, both of which are corrections to things stated earlier.

---

## 1. Before and after

| | RAW | CLEAN |
|---|---|---|
| Mean price | $3.57 | $3.48 |
| SD of price | $0.664 | $0.588 |
| **Finding A: Class I diff on %Black, raw** | +0.0353 (t +29.02) | **+0.0362 (t +28.03)** |
| **Finding A: + income, log(pop)** | +0.0353 (t +27.68) | **+0.0354 (t +26.14)** |
| price on %Black, no FE | −0.00240 (t **−3.60**) | **−0.00098 (t −1.62)** ⚠ |
| price on %Black, state FE | −0.00352 (t −7.02) | −0.00374 (t −7.09) |
| **zone / override variance split** | 58.9% / 41.1% | **43.7% / 56.3%** ⚠ |
| burden (cost/income) on %Black, state FE | +0.00286 (t +12.25) | +0.00288 (t +11.91) |
| median income on %Black, state FE | −$366 (t −13.44) | −$359 (t −12.93) |
| Class I pass-through, within state | 0.38× (t +1.51) | 0.44× (t +1.68) |
| state explains ln(price) | 53.5% (51 groups) | 41.2% (43) |
| county explains ln(price) | 90.8% (1,727) | 88.6% (1,545) |

## 2. The two things that changed

### ⚠ The raw price-race gradient was partly Virginia

Unconditionally, price on %Black moves from **−0.00240 (t −3.60)** to **−0.00098 (t −1.62)** —
from significant to null. Virginia is the cause: 117 stores, **18.8% mean %Black** (by far the
highest of any excluded state), at a statutorily compressed **$3.64**. A high-Black,
low-and-fixed-price state was pulling the unconditional correlation negative.

**Correction:** statements elsewhere that Blacker communities pay *less* for milk should be
restricted to the **within-state** result, which is unaffected (t −7.09) and is the one that
matters anyway. Unconditionally the national gradient is now indistinguishable from zero. This
does not help the memo — null is not positive — but it was overstated in the other direction and
should be fixed.

### ⚠ The local layer is the majority, not the minority

The zone/override variance split goes from **58.9 / 41.1** to **43.7 / 56.3**. The excluded
states were the most compressed in the country — several with literally one price — so they
inflated the between-state share. With them gone, **the majority of variation in what a Walmart
shopper pays is store-level, not state-level.**

**Correction to `zone_vs_override.md`:** "roughly three-fifths centrally set, two-fifths local"
becomes **roughly 44% coarse-geographic, 56% store-level**. This *strengthens* the point that
section made — Finding B tests the store-level layer, and that layer is now the larger one —
while making the earlier arithmetic wrong. Both are recorded.

## 3. What did not change

- **Finding A is unaffected and marginally stronger**: +0.0362 (t 28.03) raw, +0.0354 (t 26.14)
  under controls. Dropping every state whose milk price is set by statute leaves the federal
  Class I result exactly where it was. That is a meaningful robustness check — Finding A is
  about the federal schedule, and it survives removing all state-level interference.
- **Finding B is untouched.** None of SC, LA, MS, AR, NC, AL, GA, TN or TX is excluded, so every
  coefficient is identical: LA +0.00418 (t +2.72) with no FE, +0.00028 (t +0.37) under ZIP3
  region FE; SC +0.00164 (t +0.33) / −0.00868 (t −1.56). The conclusions in
  `walmart_pricing_geography.md` §4 stand.
- **The burden decomposition holds**: burden on %Black +0.00288 (t +11.91), income −$359 per
  point (t −12.93). The affordability disparity is still the income denominator.

## 4. What was dropped

| State | Stores | Mean | Distinct prices | Mean %Black |
|---|---|---|---|---|
| PA | 134 | $5.07 | 7 | 4.5 |
| **VA** | 117 | $3.64 | **2** | **18.8** |
| NJ | 58 | $4.43 | **1** | 8.6 |
| ME | 22 | $4.95 | **1** | 0.9 |
| MT | 15 | $3.90 | 3 | 0.5 |
| ND | 14 | $3.95 | **1** | 3.4 |
| HI | 10 | $6.28 | **1** | 1.7 |
| AK | 7 | $4.98 | **1** | 4.5 |

Six of the eight have one to three prices statewide. Virginia is the one that mattered
statistically, for the reason in §2.

## 5. Using it

```python
from milk_pricing.panel import load, EXCLUDED
S = load()                 # clean panel, 3,768 stores
R = load(exclude=False)    # raw, for before/after
```

`src/milk_pricing/panel.py` carries the exclusion list and the reason for each state.
Existing analysis scripts still read the raw file directly; they are unaffected in substance
(all use state or finer fixed effects) but should migrate to `panel.load()` if extended.

## Reproduction

`analysis/clean_panel.py` prints the full before/after table.
