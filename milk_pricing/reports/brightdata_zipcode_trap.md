# The Bright Data Walmart "zipcodes" template pins the store but not the price

**Date:** 2026-08-24 · Branch `claude/walmart-milk-pricing-sc-m7zc99`
**Question:** pull SC Walmart stores via Bright Data's Walmart template, which takes ZIP codes

**Bottom line: the template exists, it works, and its prices cannot be used.** Bright Data's
**"Walmart - products zipcodes"** scraper (`gd_m693oc1r1gebnayxq`) accepts a `zip_code` field
and resolves a genuine local store from it. But the price it returns is Walmart's **national
online price** — `promotion_fulltext: "Price when purchased online"` — not the store shelf
price. Chocolate milk came back at **$3.63 in Pittsburgh, Spartanburg, Hilton Head, Chicago and
Sacramento alike**; vegetable oil at **$4.18** in all five.

**This is a trap, not a dead end.** The records look immaculate — real store names, per-store
stock counts, per-store delivery ETAs. A South Carolina pull through this template would produce
a clean-looking file in which every store has the same milk price, and the honest reading of that
file would be "SC has no store-level variation," which is false.

---

## 1. I was using the wrong scraper — that part was my error

My earlier note in `reports/walmart_basket_national.md` said the Dataset API "silently drops
`zipcode`." That was accurate for `gd_l95fol7l1ru6rlo116` ("Walmart - products"), which is what
I had tried, but it was the wrong scraper and the wrong field name. The account holds five
Walmart scrapers:

| id | name |
|---|---|
| `gd_l95fol7l1ru6rlo116` | Walmart - products |
| **`gd_m693oc1r1gebnayxq`** | **Walmart - products zipcodes** |
| `gd_m7ke48w81ocyu4hhz0` | Walmart sellers info |
| `gd_m7khey0wb7wviejgj` | Walmart products search |
| `gd_mpql1v8g2o8o6l1wzd` | Walmart Reviews |

The field is **`zip_code`**, not `zipcode`. (The trigger endpoint's validation error names the
schema, which is the quickest way to discover it: send a deliberately malformed row and read the
`errors` array.)

## 2. Store resolution works

Requested ZIP → store actually resolved:

| ZIP requested | Store returned |
|---|---|
| 29201 | Cayce Neighborhood Market, West Columbia 29033 |
| 29601 | Greenville Wade Hampton Blvd Neighborhood Market, 29615 |
| 29926 | Hilton Head Island Supercenter, 29926 |
| 29306 | Spartanburg Cedar Springs Rd Neighborhood Market |
| 29566 | North Myrtle Beach Supercenter |
| 16335 | Meadville Supercenter |
| 17055 | Camp Hill Supercenter |
| 15227 | West Mifflin Supercenter |

Real stores, correct areas, with `pickup_address`, `pickup_zipcode`, `stock_quantity` and a
`delivery_eta` naming the store. The geographic targeting is genuine.

## 3. The price is not

Validated against 8 ZIPs whose Walmart shelf price is already known from the existing
collection:

| ZIP | Template price | Known shelf price | Match |
|---|---|---|---|
| 29306 Spartanburg SC | $3.52 | $2.32 | no |
| 29607 Greenville SC | $3.52 | $2.50 | no |
| 29926 Hilton Head SC | $3.52 | $3.86 | no |
| 29566 N Myrtle Beach SC | $3.52 | $3.97 | no |
| 17055 Camp Hill PA | $3.52 | $4.63 | no |
| 16335 Meadville PA | $3.52 | $4.94 | no |
| 15227 Brentwood PA | $3.52 | $5.17 | no |
| 95829 Sacramento CA | $3.52 | $3.52 | **yes** |

One match out of eight, and it is coincidence: $3.52 is simply the national online price, which
happens to equal Sacramento's shelf price.

**The decisive proof is Pennsylvania.** The Pennsylvania Milk Marketing Board sets a *minimum
retail* price for milk. Observed PA shelf prices run $4.63–$5.48. **A Pennsylvania store cannot
legally sell whole milk at $3.52**, so $3.52 is definitionally not a PA shelf price.

Confirmed across products and geography — 5 ZIPs spanning Pittsburgh, Spartanburg, Hilton Head,
Chicago and Sacramento:

| Item | Distinct prices across all five |
|---|---|
| GV 1% chocolate milk | **1** — $3.63 everywhere |
| GV vegetable oil 48 oz | **1** — $4.18 everywhere |
| GV whole milk | 3 — $3.12 / $3.52 / $3.53 |

The small milk spread is not geography either: ZIP 15227 (Pittsburgh) resolved to **"Old Saybrook
Store"** — Connecticut — so store resolution is not perfectly reliable, and Sacramento returned
$3.52 on one run and $3.12 on another for the same SKU at the same store.

Every price field was checked. `final_price` 3.52, `price_range` null, `shipping_price` null,
`unit_price` 0.028/fl oz (= $3.58/gal, internally consistent with the online price). There is no
hidden local price in the record.

The `Walmart products search` scraper does not accept `zip_code` at all — its schema takes `url`
only.

## 4. The trade-off, stated plainly

| Scraper | Store control | Price realism |
|---|---|---|
| `Walmart - products` (proxy exit) | **none** — random US store | **real** shelf prices |
| `Walmart - products zipcodes` | **yes** — pick the ZIP | **national online price only** |

The first one's prices are demonstrably real: it returned $2.72 in Chicago up to $5.17 in
Brentwood PA, **with Pennsylvania stores clustering at the top exactly as the regulated floor
requires**. That independent reproduction of PA's regulatory structure is what validates it.

So Bright Data can give you the store or the shelf price, not both. Neither path yields
store-level shelf prices for South Carolina.

## 5. What this says about the existing national file

The 4,149-store file ranges **$2.32 to $5.48 with PA at the top** — real shelf-price structure
that the zipcodes template cannot produce. **Whatever method produced it captured in-store
prices, and it is the only source in this project that does.** That is worth knowing precisely,
because the entire retail theory rests on it: it would be worth confirming what that pipeline
actually read (shelf price vs. online price vs. pickup price), since a mixed source would be a
serious problem and a uniformly online source would have shown no variation at all — it does, so
it is not that.

## 6. Where this leaves the SC question

Still unanswered, and now for a well-characterised reason rather than a vague one. To get SC
store-level prices for a basket, the options are:

1. **The existing collection method** — it demonstrably reads shelf prices. Adding the 13 SKUs
   (listed in `analysis/walmart_basket_national.py`) is the shortest path.
2. **A geo-targeted proxy zone** — residential/ISP with `country-state-city` in the proxy
   username, driving `src/milk_pricing/sources/walmart_basket.py`, whose `StoreMismatch`
   verification would then be meaningful. This account has only an ungeotargeted `unblocker`
   zone.
3. **Not the zipcodes template**, for the reason above — and if anyone else on the team reaches
   for it, this report is why they should not.

## Reproduction

`analysis/bd_zipcode_probe.py` (requires `BRIGHTDATA_API_TOKEN`). Snapshots from this
investigation: `sd_mt70j5xw2j429iv2l6`, `sd_mt70pogcccpw4kitc`, `sd_mt70wzbp1sbnhn24dv`.
