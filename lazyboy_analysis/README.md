# La-Z-Boy competitive pricing scrape

Public pricing for La-Z-Boy and its competitive set, collected from multi-brand
retailers rather than from brand websites.

## Why scrape retailers instead of brand sites

Most of the competitive set is wholesale-only and publishes no retail price at
all. Checked directly:

| Brand | Own site | Price published? |
|---|---|---|
| Flexsteel | Shopify | No — `products.json` returns `$0.00`; dealer-priced |
| Southern Motion | WordPress | No — dealer locator only |
| Best Home Furnishings | custom | No |
| Catnapper | custom | No |
| Palliser | custom | No |
| Bassett | Salesforce Commerce | Yes, but no clean feed |
| Natuzzi | custom | Blocked (403) |
| Stressless | custom | JS-rendered, no static price |
| La-Z-Boy | custom | Yes — per-cover prices in static HTML |

Slumberland and Steinhafels both run Shopify, whose `/products.json` exposes
brand, price, list price, SKU and variants as structured data. They also stock
La-Z-Boy *and* its competitors side by side, so brands can be compared on the
same shelf, under the same promotional calendar, in the same market. That
controls for retailer effects in a way that comparing brand-site MSRPs cannot.

## Scripts

```bash
python3 scrape_retailers.py --out data        # full Shopify catalogues
python3 fetch_categories.py --out data        # Steinhafels category membership
python3 build_dataset.py --data data --out data/catalog.csv
python3 analyze.py --catalog data/catalog.csv
python3 scrape_lazboy_covers.py --out data/lazboy_covers.csv
python3 match_channels.py                     # three-channel comparison
python3 build_skus.py --data data --out data/skus.csv
python3 teeup.py --skus data/skus.csv --brand La-Z-Boy
python3 teeup.py --skus data/skus.csv --brand Flexsteel
python3 ladder.py --skus data/skus.csv --brand La-Z-Boy
```

## Data

- `data/catalog.csv` — 1,672 rows, 8 brands, both retailers. Brand, form,
  motion, material, price, list price, discount.
- `data/lazboy_covers.csv` — 205 cover-level prices across 34 La-Z-Boy
  products, from La-Z-Boy.com's own `data-cover-price` attributes.

Steinhafels labels vendors with four-letter codes; these were resolved by
reading its own brand collections, not guessed:
`LAZB`=La-Z-Boy, `FLEX`/`FLXD`=Flexsteel, `HGTV`=Bassett (the licensed HGTV
Home Design Studio line), `BSCH`=Best Home Furnishings, `NATU`=Natuzzi,
`SOMO`=Southern Motion, `JACK`=Jackson/Catnapper, `ASHY`=Ashley.

## Three-channel comparison

`match_channels.py` matches La-Z-Boy models across La-Z-Boy.com, Slumberland
and Steinhafels — the three-retailer view. The three channels use different SKU
schemes, so the join key is model family + form + drive type ("Pinnacle /
Recliner / Manual"), which is same-model-same-configuration, not same-SKU.

Headline: on 27 matched configurations, dealers **list** the same model a median
**+43%** above La-Z-Boy.com and **sell** it a median **-25%** below. Same frame,
a 68-point swing.

The list-side number is inflated by cover grade — La-Z-Boy.com's figure is its
cheapest cover, while a dealer stocks a specific and often higher one. That bias
runs the other way on the sale side, which makes the -25% the conservative,
robust half of the finding. What neither explains is the dispersion: identical
model and configuration ranges from -50% to +50% depending on where you buy it.

## Assortment and ladder position

`build_skus.py` expands the catalogues to SKU level (2,643 rows); `teeup.py`
reports what each retailer carries and where La-Z-Boy sits in its price ladder.

For each La-Z-Boy SKU it finds the competitor SKUs in the same store and
category priced within one step above it, and ranks the SKU against that
competitor price distribution. Three roles fall out: **opening price point**
(bottom quartile), **mid-ladder**, **premium anchor** (top quartile).

Only 8 of 244 La-Z-Boy SKUs are opening price points. The rest sit mid-ladder
(173) or above most of the competitive set (63). La-Z-Boy is not being used as
a cheap draw at either retailer.

Two things this measures carefully, and one it does not:

- Competitor **models** are counted, not colourways — six covers of one sofa is
  one alternative on the floor.
- Role is assigned by percentile, so it is invariant to the step-up window; at
  +15%, +30% and +50% the split is identical and only the counts scale.
- It does **not** measure intent. "Tees up N competitors" means N competitor
  models sit one step above in the same store and category. Whether the
  retailer merchandises it that way is not observable from a catalogue feed.

A raw step-up count on its own is misleading: the highest counts belong to
mid-ladder SKUs that simply sit where competitor prices are dense. Position and
count have to be read together, which is why the entry-point table filters to
the bottom quartile first.

## Where each brand sits

`ladder.py` answers two questions that can disagree, so it reports them apart:
each brand's median indexed to the focus brand (structural position), and how
many competitor models sit within one step below versus above the focus
brand's own SKUs (adjacency). A median hides overlap when two brands span a
wide range; adjacency catches it.

The two retailers agree on the shape. Flexsteel is the ceiling — 119% to 211%
of La-Z-Boy depending on store and category, with nothing above it but Bassett.
La-Z-Boy holds the middle. Ashley is the floor at 22% to 53%. Run with
`--brand Flexsteel` and every brand in the set undercuts it except Bassett.

The exception worth knowing is Southern Motion, which is not one position but
two: it undercuts La-Z-Boy on sofas and loveseats (91-95%) and sits well above
it on recliners (172% at Slumberland). A single index figure would have
averaged that away into "roughly level".

`teeup.py --brand Flexsteel` finds zero entry-point SKUs against La-Z-Boy's
eight: 165 of 181 Flexsteel SKUs are premium anchors. Flexsteel never plays the
value role at either retailer.

## Caveats

- **Not carried, so not covered:** Palliser and Stressless appear at neither
  retailer. Catnapper appears only via its parent, Jackson Furniture.
- **Shopify caps collection feeds at 250 products**, so Steinhafels category
  membership is supplemented by parsing the category path out of each product
  handle.
- **Material is unresolved for 49% of rows.** Upholstery is often named only in
  the description or the colourway. Fabric-vs-leather cuts below that coverage
  should be treated as directional.
- **La-Z-Boy.com renders only 36 products per category server-side** and the
  rest is JS-paginated, so the cover file is a 34-product sample, not the line.
  Only 6–7 covers per product load statically, so the within-frame price spread
  it shows is a floor, not the true range.
- **Channel matches are model-level, not SKU-level**, and n=27. Treat individual
  rows as leads to verify against internal data, not as settled numbers.
- Parts and add-ons (handles, bases, sheet sets) carry a seating category in
  the feed and are excluded by title, not by a price floor, so that genuinely
  cheap furniture is kept.
- Prices are a single snapshot and furniture promotions move weekly. Re-run
  before quoting any number externally.
