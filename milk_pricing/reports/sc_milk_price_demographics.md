# Milk price and ZIP demographics — South Carolina

Tests whether the milk prices collected in this project vary with the racial composition of the ZIP served. Demographics are ACS 5-year (B03002 race, B19013 median household income) via Census Reporter, joined to the benchmark private-label whole gallon.

**Headline: no evidence that Aldi charges more in ZIPs with a higher Black population share. The Walmart sample is far too small to support any claim, and what signal it contains tracks income and rurality more strongly than race.**

## Aldi — 350 ZIPs, no race-linked price gap

The original version of this section rested on 18 ZIPs across three metros and
concluded that Aldi prices metros as flat zones, so demographics could not
enter the price. The flat-zone claim was wrong — a full 538-ZIP sweep shows
Aldi's SC whole-gallon price ranging **$2.19–$4.19** — but the substantive
finding survives on far better evidence.

Joining the sweep to ACS gives **n = 350** SC ZIPs with both a price and
demographics:

| Relationship | Pearson | Spearman | t |
|---|---:|---:|---:|
| Black share vs price | **-0.011** | +0.020 | 0.21 |
| Median income vs price | +0.035 | -0.031 | 0.66 |

At n=350, |t| above ~1.97 would be significant at p<0.05. Neither comes close.

Median price by Black-share quintile:

| Quintile | Black share | n | Median $/gal |
|---|---|---:|---:|
| Q1 | 0.0–8.7% | 70 | $2.90 |
| Q2 | 8.8–19.7% | 70 | $2.90 |
| Q3 | 19.7–29.2% | 70 | $2.95 |
| Q4 | 29.2–44.1% | 70 | $2.95 |
| Q5 | 44.3–100% | 70 | $2.95 |

A five-cent spread from the whitest to the Blackest quintile of South Carolina
ZIP codes, with no monotonic trend. Income quintiles are equally flat
($2.89–$2.95 from poorest to richest).

Aldi's SC price does vary — by two dollars a gallon across the state — but that
variation is uncorrelated with either the racial composition or the median
income of the ZIP. Whatever drives it is something else.

## Walmart — underpowered, and confounded

| ZIP | City | Black share | Median income | $/gal |
|---|---|---:|---:|---:|
| 29349 | Inman | 8.7% | $76,168 | $2.17 |
| 29650 | Greer | 9.3% | $94,522 | $2.36 |
| 29501 | Florence | 35.6% | $71,671 | $2.67 |
| 29526 | Conway | 13.6% | $68,825 | $2.74 |
| 29579 | Myrtle Beach | 7.9% | $79,644 | $2.74 |
| 29627 | Belton | 11.6% | $59,167 | $2.74 |
| 29853 | Williston | 44.0% | $44,983 | $3.72 |

| Relationship | Pearson | Spearman | Excl. Williston |
|---|---:|---:|---:|
| Black share vs price | +0.759 | +0.429 | +0.29 |
| Median income vs price | **-0.814** | **-0.714** | **-0.54** |

Three reasons not to read the +0.759 as a race effect:

1. **It is one store.** Drop Williston and it collapses to +0.29. Spearman is +0.429 against Pearson +0.759, which is the signature of a single outlier rather than a monotonic trend.
2. **Income is the stronger and more robust relationship** on every measure (-0.814 / -0.714, still -0.54 without Williston).
3. **Williston is rural.** Population 31k ZIP, no discounter nearby — the competitive-intensity story already established in the SC report. In South Carolina rurality is correlated with both lower income and higher Black share, so with n=7 these three cannot be separated.

With seven opportunistically-sampled stores, this analysis can rule nothing in and nothing out.

## Correction: the "no competition" claim was wrong

An earlier version of this report concluded that Williston's high price reflected
an absence of competition, and called that the one finding that held. That was
not supported, and it is withdrawn.

What was actually established was the absence of **Aldi**, because Aldi is what
this project collects. That was then written up as the absence of *competition*,
which is a different and much larger claim — and a wrong one. Verified since:

| Retailer | Williston (29853) | Source |
|---|---|---|
| Dollar General | present | store page confirmed |
| Family Dollar | present | store page confirmed |
| Walmart | present (store 795) | sampled, $3.72/gal |
| Aldi / Lidl | not present locally | absent from collection |

Walmart's own store-795 page lists Barnwell, Aiken and Orangeburg as adjacent
trade areas, so the surrounding retail set is wider still.

The retailer universe in `markets.py` never included the **dollar channel** —
Dollar General, Family Dollar, Dollar Tree — or rural independents such as
Piggly Wiggly and IGA. In a town of Williston's size those are the grocery
competitive set, and omitting them meant "not in my retailer list" was silently
being read as "not in the market."

**What remains open.** Dollar General does sell milk, and its price in Williston
is unknown: its site is client-rendered and does not expose per-store prices, so
this project has not measured it. Until it is measured, we cannot say whether
Walmart's $3.72 is the local low, the local high, or in the middle. The claim
that Williston shoppers face a worse milk price than Inman shoppers rests
entirely on the Walmart-to-Walmart comparison, which is real ($2.17 vs $3.72,
same SKU, same chain) — but the shopper's actual best local option is not
established.

**Dollar-channel prices, measured.** Dollar General's product sitemap is
readable (32,475 products, 167 candidate dairy-milk URLs) and its Bright Data
dataset returns prices:

| Product | Size | Price |
|---|---|---:|
| Meadow Gold Whole Milk w/ Vitamin D | 1 gal | $3.25 |
| Meadow Gold 2% | 1 gal | $3.20 |
| Cascade Homogenized Whole Milk | 1 gal | $4.00 |
| Price's Whole Milk | half gal | $2.00 |
| Lehigh Valley Whole Milk | half gal | $1.40 |

**This bracket ($3.20–$4.00 a gallon) straddles Walmart's Williston price of
$3.72.** Two caveats keep it from being a Williston number: the records carry
`store_id: None` and `zipcode: None`, so they are default-catalog prices with no
store context, and the brands are regional dairies from outside the Southeast
(Meadow Gold, Cascade, Creamland, Lehigh Valley), which means the catalog is
defaulting to some other region entirely.

It is still enough to retire the assumption underneath the original claim. I had
reasoned that dollar stores would not discipline milk price the way a hard
discounter does. On these numbers Dollar General sells gallon milk in the same
band Walmart charges in Williston, and possibly below it. Walmart is not
self-evidently the low-price option there.

Note also that DG carries national and regional dairy brands rather than a
private-label white gallon — the only Clover Valley white milk in the sitemap is
a 64 oz lactose-free. So a DG-to-Walmart comparison is brand-tier mismatched:
Great Value against Meadow Gold. For a Williston shopper choosing where to buy a
gallon, the tier mismatch does not matter; for a like-for-like pricing
benchmark, it does.

**Family Dollar and Dollar Tree could not be measured.** Both run fully
client-rendered storefronts that expose no products or prices in server HTML
(Family Dollar returns a 17 KB shell with no title). No Bright Data dataset
exists for Family Dollar; the Dollar Tree dataset supports no discovery mode,
and its sitemap host is unreachable. Their Williston milk prices, if they carry
milk at all, remain unknown.

**What survives.** Two narrower statements are still supported: Walmart charges
$1.55/gal more at its Williston store than at its Inman store on the identical
SKU, and Aldi — whose presence coincides with Walmart's lowest SC prices — does
not operate in Williston. Whether the dollar channel exerts the same downward
pressure on milk that a hard discounter does is a genuine open question, and it
is the specific thing that would need measuring before any access argument can
be made.

## Limits

- Walmart n=7, not a designed sample; no ZIP-level Walmart pricing (store follows proxy exit, and Walmart's own zipcode input is ignored).
- Aldi figures are its Instacart-powered delivered price, which may differ from shelf price, and Aldi's ZIP coverage is truncated by where it operates.
- Publix, Food Lion and Harris Teeter are absent (blocked), so the conventional channel — which serves a different customer mix — is untested.
- ZCTA boundaries approximate postal ZIPs, and a store serves a trade area, not a ZIP. Assigning one ZIP's demographics to a store is a rough proxy.
- Correlation on 6-7 points is descriptive only. Nothing here is a significance test, and it should not be cited as one.