# Which number came from where

**Date:** 2026-08-24 · Branch `claude/walmart-milk-pricing-sc-m7zc99`

Every finding in this project traces to one of five datasets, and they are not interchangeable.
An opposing expert will ask this first, so it is written down.

**The short answer: every substantive finding runs on the client's two uploaded files. Nothing
I collected has ever supplied the price series for a racial test.** My collections answer a
different question — whether milk is priced differently from other goods — and today's SC pull
turned out to measure a different price object entirely.

---

## 1. The five datasets

| File | Origin | What the price is | Used for |
|---|---|---|---|
| `sc_walmart_official.csv` (92 stores) | **client upload** | **in-store shelf price** | all SC analysis of record |
| `national_walmart_official.csv` (4,149) | **client upload** | **in-store shelf price** | Findings A & B, metros, zones, PA |
| `aldi_sc_observations.json` (20 stores × 25 items) | my collection, Instacart via Bright Data | Aldi delivery price | the three-tier dairy pattern |
| `walmart_basket_national.csv` (247 obs) | my collection, BD *Walmart – products* | shelf price, **random store** | cross-product dispersion |
| `sc_basket.csv` (1,191 obs) | my collection, BD *Walmart – products zipcodes* | **online price** | today's SC basket |

Dependency map, from the scripts themselves:

- **Client shelf data →** `zone_override.py`, `within_metro.py`, `pricing_unit.py`,
  `sc_variation.py`, `pa_minimum_pricing.py`, `fb_within.py`, `metros.py`, `txca_memo.py`,
  `hisp_fe.py`, `ca_sens.py`, `basket_test.py`
- **My collections →** `dairy_pattern.py`, `walmart_basket_national.py`, `sc_basket.py`

Every racial coefficient the memo would cite — Finding B, the metro tests, the zone/override
split, the SC metro discount, the PA analysis — comes from the first group.

## 2. The two SC series measure different things

Both are "Walmart whole milk by SC store," both cover the same 92 stores:

| | Client upload | My BD zipcode pull |
|---|---|---|
| Range | $2.32 – $4.00 | $1.97 – $5.31 |
| Distinct prices | 21 | 25 |
| Mean | $3.11 | **$3.54** |
| Correlation between them | | **r = +0.065** |
| Exact matches | | **1 / 92** |
| **Mean absolute difference** | | **$0.67** |

They are essentially unrelated. The client's file is the shelf price; mine is labelled `"Price
when purchased online"` on 1,188 of 1,191 records, and it runs **$0.43 higher on average**.

Two independent proofs that the client's series is the shelf price and mine is not:

1. **Pennsylvania.** The BD series reports $3.52 at PA stores. The PA Milk Marketing Board sets a
   *minimum retail* price and the client's file shows PA at $4.63–$5.48. A PA store cannot
   legally sell whole milk at $3.52.
2. **Structure.** The client's national file reproduces known regulatory geography — PA at the
   top, the state milk-control states compressed to one or two prices. A national online price
   book cannot produce that.

## 3. The part worth stating plainly

**My first attempt at this, before the client's upload, was wrong — and today's investigation
explains why.**

That early sample was collected through Bright Data's Web Unlocker. The client caught it: the
ZIP was wrong in 5 of 7 rows and prices ran $0.14–$0.15 low. It was withdrawn and the client
uploaded their own file, which has been the basis of everything since.

The cause is now characterised rather than guessed: that Bright Data account has one
ungeotargeted `unblocker` zone, so the serving store is whatever the proxy exit resolves to.
Today the same defect reappeared in a new form — a 295-SKU catalogue that looked national but
was 295 items at one Sacramento store — and it is documented in
`reports/brightdata_zipcode_trap.md`. **I made the same class of error twice, four days apart.
The second time it was caught before it reached a finding.**

## 4. What this means for the case

- **The retail theory rests entirely on the client's collection.** That pipeline is the single
  point of failure for Finding B and everything downstream, and it has never been independently
  reproduced — because, as this project now establishes, Bright Data cannot reproduce it.
- **It would be worth confirming exactly what that pipeline read** — shelf price, pickup price,
  or online price — and whether it read consistently across all 4,149 stores. The evidence says
  shelf price (PA reproduces correctly, and an online book would be flat), but "the evidence is
  consistent with it" is weaker than knowing.
- **My collections corroborate the mechanism, not the disparity.** Aldi's SC panel, the national
  Walmart sample and the SC online book all show fluid milk priced store-by-store while adjacent
  dairy is priced nationally. Three datasets, two retailers, two price books — that finding does
  not depend on the client's file. The racial null results do.

## Reproduction

`python3 analysis/sc_basket.py` prints the SC series comparison. The dependency map above was
generated by grepping each script in `analysis/` for its inputs.
