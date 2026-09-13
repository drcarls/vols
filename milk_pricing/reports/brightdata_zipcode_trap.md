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

Adding **`store_id`** alongside `zip_code` changes nothing. Tested through the synchronous
`/datasets/v3/scrape` endpoint with `{"input":[{url, zip_code, store_id}], "limit_per_input":null}`
— the exact documented call shape — against four stores with known shelf prices:

| ZIP | store_id sent | Store resolved | Template price | Known shelf |
|---|---|---|---|---|
| 29607 | 640 | Greenville Woodruff Rd Supercenter | $3.52 | $2.50 |
| 29926 | 728 | Hilton Head Island Supercenter | $3.52 | $3.86 |
| 15005 | 4643 | Baden Supercenter (PA) | $3.52 | — |
| 15010 | — | Beaver Falls Supercenter (PA) | $3.52 | — |

0 of 4, every one tagged `"Price when purchased online"`.

The `Walmart products search` scraper does not accept `zip_code` at all — its schema takes `url`
only.

### And the reverse: `store_id` on the scraper that *does* return real prices

`Walmart - products` (`gd_l95fol7l1ru6rlo116`) **accepts** a `store_id` field — it passes
validation — but **ignores it**. Requesting `store_id: "640"` (Greenville Woodruff Rd, SC)
returned `store_id: 3081`, `store_name: "Sacramento Supercenter"`, at $3.52. The proxy exit wins.
It rejects `zip_code` outright.

That closes the matrix:

| Scraper | `zip_code` | `store_id` | Store control | Price |
|---|---|---|---|---|
| `Walmart - products` | rejected | accepted, **ignored** | none | **real shelf price** |
| `Walmart - products zipcodes` | **required, honoured** | accepted | **yes** | national online only |
| `Walmart products search` | rejected | — | none | — |

The one that honours geography returns the wrong number; the one that returns the right number
ignores geography.

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

---

## 7. Addendum: the full South Carolina pull, run anyway

Run at the client's direction across **all 92 SC Walmart stores** (`zip_code` + `store_id`, GV
whole milk gallon, via `/datasets/v3/scrape`). Data: `data/sc_bd_zipcode_milk.csv`.

**74 of 92 returned a price**; 18 failed with `store_id <id> not available for zip <zip>` — the
store IDs in `sc_walmart_official.csv` do not always match the IDs Bright Data resolves for that
ZIP (its error helpfully names the ones it *does* have, e.g. `store_id 6174|628 not available for
zip 29485`). Dropping `store_id` and letting the ZIP resolve alone would recover those 18.

At full scale the picture is more nuanced than the 5-ZIP probe suggested — but not more usable:

| | |
|---|---|
| Distinct prices returned | **16**, $2.72–$4.23 |
| Records at the $3.52 national default | **56 of 74 (76%)** |
| Correlation with the known SC shelf price | **r = +0.178** |
| …among only the 18 deviating records | r = +0.342 |
| Records matching the known shelf price | **0 of 74** |

So it is not purely a constant — about a quarter of stores return something else — but the
deviations do not track reality. Individual errors are large and two-signed: Taylors **+$1.58**,
Aiken **+$0.86**, Columbia Forest Drive **+$0.86**, against Cheraw **−$0.75** and Laurens
**−$0.70**. Every priced record still carries `"Price when purchased online"`.

**For comparison, the same 92 stores in the reference file span $2.32–$4.00 across 21 distinct
prices.** The two measurements share almost no information.

### The one genuinely useful result

Both datasets were regressed on ZIP racial composition over the **same 74 SC stores**, income
controlled:

| Price measure | %Black coefficient |
|---|---|
| Bright Data zipcode template | +0.00184 (t **+0.89**) |
| Known SC shelf price | −0.00046 (t **−0.09**) |

**Two independent measurements of SC Walmart milk, one of them badly contaminated, and both
return null on race.** That is a weak form of robustness — a contaminated instrument agreeing
with a clean one is not strong evidence — but it points the same way as everything else in this
project: `why_sc_varies.md` (SC's spread is a metro discount, %Black t = −0.13),
`within_metro_test.md` (Atlanta null, permutation p = 0.65), and `zone_vs_override.md` (SC rural
t = +0.33).

**Conclusion for the SC question: the scrape is done, the price field cannot support the
analysis, and the analysis it cannot support was already null on the clean data.**

---

## 8. Re-verified 2026-09-12: nothing has changed

Asked whether store-level Walmart milk can still be collected. Re-tested rather than recalled,
on the same account token. Everything below is today's output, not the August record.

**Account state.** Auth valid (`/status` 200). `GET /zone/get_active_zones` returns exactly
one zone: `[{"name":"unblocker","type":"unblocker"}]`. No residential or ISP zone, so no
`country-state-city` targeting. This is the single fact that decides the answer.

**Web Unlocker page path** (real shelf prices, store set by proxy exit). Five requests for the
same SKU:

| payload | result |
|---|---|
| baseline, no geo | 200, 475,866 bytes — store **3081, Sacramento 95829** |
| `country: "us"` | 200, 475,576 bytes — store **3081, Sacramento 95829** |
| `country` + `state: "sc"` | 200, **empty body** |
| `country` + `state` + `city: "columbia"` | 200, **empty body** |
| `zip: "29201"` | 200, **empty body** |

Note the shape of the failure, because it is easy to misread in both directions. `state`,
`city` and `zip` **pass request validation** — send `geo` or a nonsense field instead and the
API returns a 400 naming it as `"not allowed"`, while these return 200. They are real fields;
this zone simply has no entitlement to serve them, so the response body is empty. `country`
resolves but only to a country, which does not pin a store. August's note that these were "not
valid fields for this zone" understated it slightly: they are valid fields, unserviceable on an
unblocker zone. The operational conclusion is unchanged.

**A transport artifact that nearly produced a false finding.** The first pass of this probe used
curl's default HTTP/2 and returned `curl: (92) Invalid HTTP header field ... [proxy-connection]`
for exactly the geo-bearing requests — the agent proxy, not Bright Data. Read at face value it
looks like the API accepted the geo fields and something downstream broke, i.e. the opposite of
the truth. `--http1.1` resolves it. Any future probe from this environment must use it.

**Dataset zipcode template** (`gd_m693oc1r1gebnayxq`, real stores, online prices). Re-ran
`--validate`, snapshot `sd_mtydchx927xrzfd16y`, 8 records, 0 errors:

| zip | template | known shelf | match |
|---|---|---|---|
| 15227 Brentwood PA | $3.52 | $5.17 | no |
| 16335 Meadville PA | $3.52 | $4.94 | no |
| 17055 Camp Hill PA | $3.52 | $4.63 | no |
| 29306 Spartanburg SC | $3.52 | $2.32 | no |
| 29566 N Myrtle Beach SC | $3.52 | $3.97 | no |
| 29607 Greenville SC | $3.12 | $2.50 | no |
| 29926 Hilton Head SC | $3.52 | $3.86 | no |
| 95829 Sacramento CA | $3.52 | $3.52 | **yes** |

**1 of 8**, byte-identical to August. Store resolution is still genuine (correct store names in
all 8). Pennsylvania still returns $3.52, still below the Milk Marketing Board's legal minimum,
still labelled `"Price when purchased online"`.

### Answer

**No — and it was never possible on this account.** The two capabilities live in different tools
and have never co-existed in one: the Dataset template pins the store and returns the national
online price; the Web Unlocker returns a true shelf price for whichever store the proxy exit
lands on. The 3,768-store panel underlying Finding B came from the client's own pipeline, which
this project has never reproduced.

**The unblocking step is provisioning, not code.** A residential or ISP zone with
`country-state-city` targeting, pointed at the Web Unlocker page path, is the untested
combination that would work: true shelf prices with the store forced by proxy geography. The
verification guard in `src/milk_pricing/sources/walmart_basket.py` already reads back the ZIP
the page resolved to and raises `StoreMismatch` on a mismatch, so a bad pin fails loudly instead
of filling a file with proxy-exit prices. Creating such a zone is a billable account change and
was not made here.

---

## 9. The `/store/{id}` route, tested 2026-09-13 — pins the store, cannot query a product

Asked again whether there is *any* way to get Walmart milk prices by store. §8 tested the two
routes already known. This tests a third that had never been tried, plus direct access.

**Direct access from this container is blocked by Walmart, not by the environment.** The root
`walmart.com/` returns 200, but `/ip/{sku}` returns **307 → `/blocked?url=…`** with a `_pxhd`
cookie set — **PerimeterX**. That is the bot wall Bright Data's Unlocker exists to defeat, and
it does defeat it. (The local Chromium is not an alternative: its networking fails in this
container, `ERR_CONNECTION_RESET` on every host including `example.com`.)

**The new finding: `/store/{id}` honours the store ID server-side.** Unlike every product-page
parameter, the store path resolves to the store asked for regardless of proxy exit:

| requested | store returned | city | ZIP |
|---|---|---|---|
| `/store/634` | **634** | Camden | 29020 |
| `/store/5378` | **5378** | Cayce | — |
| `/store/4440` | **4440** | Irmo | — |

Against the product page in the same session, which drifts with the exit IP — three consecutive
`/ip/10450114` calls resolved to St. Petersburg (5218), Sacramento (3081) and Idaho Falls (1902).
`?athStoreId=`, `?storeId=` and a `Cookie: ASSORTMENT_STORE_ID=` header (the `headers` field
*is* accepted by `/request`, unlike `cookies`) were all ignored.

**But no sub-path of `/store/{id}` can be queried.** Every variant returns the same store
landing page — 133–159 product names, of which one or two contain "milk" and none is Great
Value milk:

| URL | store | names | GV milk |
|---|---|---|---|
| `/store/634/search?q=milk` | 634 | 133 | 0 |
| `/store/634/search?query=milk` | 634 | 159 | 0 |
| `/store/634/search?q=Great+Value+Whole+Milk` | 634 | 143 | 0 |
| `/store/634-camden-sc/search?q=milk` | 634 | 142 | 0 |
| `/store/634/browse/food/milk/976759_976782_9159259` | 634 | 155 | 0 |
| `/store/634/browse/food/dairy-eggs/976759_976782` | 634 | 145 | 0 |
| `/browse/food/milk/…?stores=634` | — | 0 | 0 (77 bytes) |

### Why, and what would actually fix it

The returned store HTML contains **no `__NEXT_DATA__`, no `itemStacks`, no `searchResult`, no
`"products":[`** — zero occurrences of every key a rendered result grid carries. Walmart's
search and browse grids are **client-rendered**; the Unlocker's `format: "raw"` returns the
pre-JavaScript document. The `/ip/` product page, by contrast, *is* server-rendered, which is
exactly why it carries a real shelf price.

So the two halves cannot be joined on this account:

| route | store control | real shelf price |
|---|---|---|
| `/ip/{sku}` via Unlocker | ✗ exit IP decides | ✓ server-rendered |
| `/store/{id}` via Unlocker | ✓ honoured | ✗ no queryable product |
| Dataset zipcodes template | ✓ honoured | ✗ national online price |

**Two provisioning changes would each close it, and neither is code:**

1. **A JS-executing zone** (Bright Data Scraping Browser). Load `/store/{id}` to set the store,
   then navigate to `/ip/{sku}` in the same browser context and read the server-rendered price.
   This is the more likely of the two to work, because `/store/{id}` is already proven to set
   the store server-side.
2. **A geo-targeted residential or ISP zone** with `country-state-city`, steering `/ip/` by exit
   geography. The guard in `walmart_basket.py` already verifies the resolved ZIP and raises
   `StoreMismatch` on a mismatch.

**Standing answer, unchanged in substance but now for a documented reason: no store-level
Walmart shelf prices on this account.** The earlier "no" was right; it was right for an
incomplete reason, and §9 records the complete one.
