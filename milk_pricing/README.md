# Walmart SC milk pricing — Instacart via Bright Data

Pulls milk pricing for South Carolina off Instacart, normalises it to a
comparable `$/gal` benchmark, and reports where Walmart's shelf price sits
against the local competitive floor market by market.

## Why Instacart is a usable source here

Walmart's Instacart storefront is flagged **"No markups"** — Instacart shows
Walmart's own shelf prices, Rollbacks and Great Value included. That makes it a
legitimate read on Walmart shelf price rather than a marked-up delivery proxy.

The same is **not** guaranteed for other retailers: conventional and
drug-channel storefronts may carry an Instacart markup, so their numbers should
be read as *delivered price*, which is an upper bound on their shelf price. The
report states this caveat inline.

## Collection status — read this before trusting an output

Verified against the live Bright Data account (`hl_0aa1b78c`, zone `unblocker`):

| Path | Result |
|---|---|
| Web Unlocker on instacart.com | **Blocked.** Requires the zone's *Premium domains* toggle |
| Instacart Products dataset | **Product-URL only.** Search URLs return `dead_page` |
| Walmart – products dataset | **Works.** Keyword discovery returned 308 priced records |
| Walmart – price and availability | **Works.** Direct `/ip/` URLs |

**The `zipcode` input does not work.** The Walmart dataset accepts and echoes
it, but the same SKU across 11 SC ZIPs returned an identical $3.52 from an
identical `store_id` (3081). `store_id` as an input and `?store=` on the URL
were both tested and both ignored. Collection is therefore **not
geo-differentiated**, and `analyze.py`'s market-by-market output must not be
run against it — one store repeated N times would render as N markets that
agree, which reads as a finding and is an artefact. Use `ladder.py` instead
until a geo-capable source is wired in.

Keyword discovery is also **incomplete**: Great Value Whole Vitamin D Milk,
Gallon — the single most important SKU in the category — was absent from the
308-record discovery set and only appeared via a direct product URL.

## Why Bright Data is required

Instacart's storefront landing page is server-rendered, but **search and aisle
pages ship an empty shell and populate client-side**, so a plain HTTP fetch
returns zero products. Collection needs JS rendering plus per-ZIP geo pinning —
that is the Web Unlocker path in `brightdata.py`. A prebuilt-dataset path is
also implemented for large asynchronous pulls.

## Setup

```bash
export BRIGHTDATA_API_TOKEN='...'     # read from env only, never written to disk
export BRIGHTDATA_ZONE='unblocker'  # optional, defaults to unblocker
```

## Use

```bash
python -m milk_pricing.cli markets                  # show the coverage universe
python -m milk_pricing.cli collect                  # full 12 retailers x 21 ZIPs
python -m milk_pricing.cli collect --retailers walmart aldi --zips 29201
python -m milk_pricing.cli analyze                  # print the briefing
python -m milk_pricing.cli report --out reports/sc_milk_pricing.md
```

Run from `src/`, or `pip install -e .`.

## Coverage

11 SC trade areas / 21 ZIPs — Columbia, Charleston, Greenville, Spartanburg,
Myrtle Beach, Rock Hill, Florence, Anderson, Sumter, Hilton Head, Aiken.
Rock Hill and Aiken are included deliberately: they price into the Charlotte
and Augusta zones rather than an SC one.

12 retailers across five channels: Walmart; Publix, Food Lion, Harris Teeter,
Ingles, Lowes Foods; Aldi, Lidl; Sam's Club, Costco; Walgreens, CVS.

## The benchmark

Comparisons are private label vs private label, same butterfat tier, normalised
to `$/gal`. Organic, lactose-free and ultra-filtered tiers are excluded as
separate shopper decisions.

**The competitive floor is drawn from shoppable channels only** — mass,
conventional and hard discount. Club and drug prices are reported as context
but never set the floor: a Costco `$/gal` exists only behind a membership fee
and a two-gallon commitment, and a CVS 64 oz carton is a fill-in mission at a
structurally higher `$/gal`. Letting either set the floor produces confident
nonsense, so `test_club_and_drug_never_set_the_floor` pins the behaviour.

Milk is treated as a **KVI** (known value item): the analysis measures price
perception risk, not category margin.

## Actions

| Verdict | Meaning |
|---|---|
| `EXPOSED` | Walmart is more than $0.10/gal above the local shoppable floor |
| `MARGIN_LEFT` | Walmart is more than $0.10/gal below it — deeper than leadership needs |
| `HOLD` | within band; treated as intentional |
| `NO_DATA` / `NO_COMPARISON` | insufficient coverage to judge |

## Layout

```
src/milk_pricing/
  markets.py     SC trade areas, ZIPs, retailers, channels, private labels
  brightdata.py  Web Unlocker + Dataset API clients (token from env only)
  parse.py       rendered-HTML -> product rows (semantic anchors, not hashed CSS)
  normalize.py   milk classification + $/gal normalisation
  analyze.py     benchmark table, dispersion, recommendations
  report.py      markdown briefing
  cli.py         collect | analyze | report | markets
fixtures/        synthetic data for exercising the pipeline offline
```

`fixtures/synthetic_observations.json` contains **invented placeholder prices**
used only to exercise the pipeline without burning Bright Data credits. No
number in it is an observed price.

## Tests

```bash
python -m pytest tests/ -q     # 42 tests, no network required
```

The parser is additionally validated against a real captured Instacart
storefront page.
