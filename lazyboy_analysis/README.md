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

## Scope of the peer set

Everything the ladder scripts do is relative: a percentile, an adjacency count,
a price index. All of it is meaningless unless the peer set is the whole shelf.

An early version filtered the catalogues down to the nine brands originally
asked about, which turned out to be 36% of the seating on offer -- 1,038 SKUs
out of 2,872. Slumberland's second-largest seating brand (Franklin, 122 SKUs)
and Steinhafels' largest (Drew & Jonathan Home, 374 SKUs) were both missing, so
every percentile was computed against a partial floor and every "who sits below"
count understated. The pipeline now carries every vendor.

Steinhafels vendor codes that could not be resolved from its own brand
collections are kept verbatim in brackets -- `[CHRS]`, `[MOTO]` -- rather than
guessed at from product names. They count correctly in the ladder; they are
just unlabelled.

## Where each brand sits

`ladder.py` answers two questions that can disagree, so it reports them apart:
each brand's median indexed to the focus brand (structural position), and how
many competitor models sit within one step below versus above the focus
brand's own SKUs (adjacency). A median hides overlap when two brands span a
wide range; adjacency catches it.

Against the full shelf, La-Z-Boy sits mid-ladder with real traffic on both
sides. Flexsteel is the largest brand above it (119-211%), but not alone:
King Hickory, Ultra Comfort, Elran and Hooker all sit higher, and at Steinhafels
several brands price above Flexsteel itself.

Immediately below, the brand that matters is Franklin, not Ashley. Franklin
runs 89% of La-Z-Boy on recliners at Slumberland ($800 against $900) -- close
enough to be a genuine alternative for the same buyer. Ashley, at 32-53%, is a
different tier competing for a different shopper.

The exception worth knowing is Southern Motion, which is not one position but
two: it undercuts La-Z-Boy on sofas and loveseats (91-95%) and sits well above
it on recliners (172% at Slumberland). A single index figure would have
averaged that away into "roughly level".

Flexsteel has no entry-point SKUs at either retailer against the full shelf --
150 of its 181 seating SKUs are premium anchors and the other 31 are
mid-ladder. It never plays the value role.

Where it sits at the top depends on the store, though. At Slumberland it is the
ceiling: only Ultra Comfort prices above it, and then only on recliners. At
Steinhafels it is upper-mid, with a real premium tier above it -- King Hickory
(107-169), Hooker, Elran, and several unresolved codes. Steinhafels is not
simply swapping Flexsteel in for La-Z-Boy; it runs a deeper ladder overall.

Against the full shelf La-Z-Boy has 32 entry-point SKUs, not the 8 the truncated
peer set showed. The clearest cases are deeply discounted rocker recliners at
Slumberland -- Morrison, Liam and Brooks at $630-650 and 42-46% off -- each with
around 13 Franklin models priced directly above them.

## Assortment, features and materials

`assortment.py` works in the two categories where La-Z-Boy actually competes --
recliners, and motion sofas (sofas and loveseats with a reclining action, which
is how Steinhafels groups them). It answers three questions in order: how much
shelf each brand holds, how the SKUs differ, and where La-Z-Boy's own SKUs land
in the ladder that results.

**Material.** La-Z-Boy names leather in the model title and does not name
fabric. Steinhafels corroborates this independently: its variant codes carry an
LB prefix on leather and D/E/C on fabric, and across 47 La-Z-Boy models the two
never cross. So for La-Z-Boy, an unnamed cover can be read as fabric.

That convention is La-Z-Boy's, not the industry's, and an earlier version
applied it to every brand. It made Ashley look 98% fabric, when Ashley simply
names leather in the description rather than the title -- its real split is 34
leather SKUs against 22 fabric across the two categories, a +53% premium that
matches the +41% found independently in La-Z-Boy's own competitor benchmark.
Every brand except La-Z-Boy is therefore three-state, and an unnamed cover is
reported as unspecified rather than silently counted as fabric. Leather shares
remain floors: named leather only.

**Features** are counted from the title and the product description together,
out of ten named capabilities. Read from titles alone the measure mostly ranks
naming conventions: Flexsteel moves from 8th to 2nd on recliners once
descriptions are included. La-Z-Boy sits in the bottom third either way, which
is the part that survives. What this cannot do is separate a tersely listed
product from a genuinely plain one -- Barcalounger scores 0.2 on both measures
because its listings say almost nothing.

## Dealers against the brand's own store

Section 4 of `assortment.py` sets the dealer shelves beside La-Z-Boy.com. The
column that matters is covers per model: a dealer stocks 1.4-1.8 colourways of
a model, while the brand's own store shows 6.0-6.4 -- and that is only the
covers rendered server-side, so the real range is wider still.

The own-store catalogue is 226 products and 1,322 covers, reached through
subcategory pages. The top-level category pages serve a fixed 36-product set
and paginate the rest in JavaScript; an invalid subcategory path serves that
same fixed set instead of erroring, so each subcategory was verified by
checking its products link back through it, and only products carrying the
subcategory in their own URL are kept.

Ashley's own catalogue is a user-supplied export, collected through a
residential-proxy scraper -- this environment gets a 403 from every Ashley
domain, sitemaps and robots.txt included. It carries Ashley's own material
labels, which are used directly rather than re-inferred from product text. Its
"recliner" listing is a department rather than a category, so 45 third-party
nursery gliders, massage chairs and battery packs are excluded to put it on the
same footing as a dealer's recliner wall: 135 comparable products, not 180.

`scrape_manufacturers.py` does the equivalent for the competitive set, so a
dealer's model count can be read against the maker's own. Coverage is uneven
because the sites are: Flexsteel exposes a Shopify feed, Southern Motion and
Franklin expose product sitemaps, and Ashley returns 403 to everything
including robots.txt, so it is absent rather than estimated. Where a source
does not disclose whether seating is motion or stationary, the split is not
forced -- Franklin's sofas are reported as one figure. Southern Motion's are
counted as motion because the brand builds nothing else, verified on its
product pages rather than assumed from the name.

The own-store feature score reads titles only -- no descriptions were captured
-- so it is not comparable with the dealer figure, which reads both.

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
