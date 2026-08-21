# Milk price and ZIP demographics — South Carolina

Tests whether the milk prices collected in this project vary with the racial composition of the ZIP served. Demographics are ACS 5-year (B03002 race, B19013 median household income) via Census Reporter, joined to the benchmark private-label whole gallon.

**Headline: no evidence that Aldi charges more in ZIPs with a higher Black population share. The Walmart sample is far too small to support any claim, and what signal it contains tracks income and rurality more strongly than race.**

## Aldi — the clean test

Aldi is ZIP-pinned, so this compares ZIPs *inside one metro*, holding local competition, cost and urbanity roughly constant.

| Metro | ZIPs | Black share range | Prices | Result |
|---|---:|---|---|---|
| Columbia | 7 | 16.7% – 80.1% | $2.85 only | no variation |
| Greenville | 5 | 9.9% – 29.9% | $2.65 only | no variation |
| Charleston | 6 | 5.8% – 54.0% | $2.95 / $2.99 / $4.05 | varies, runs *opposite* |

Columbia is the sharpest case. Seven ZIPs spanning **16.7% to 80.1% Black** — including 29203 at 80.1% and 29205 at 16.7% — all return the **identical $2.85**. Same in Greenville. Aldi prices these metros as single zones, so neighbourhood demographics cannot enter the price at all.

Charleston is the one metro with real intra-metro variation ($1.10 on the identical SKU), and it points the other way:

| ZIP | Black share | Median income | $/gal |
|---|---:|---:|---:|
| 29405 | 54.0% | $56,600 | $2.95 |
| 29403 | 30.2% | $66,944 | $2.95 |
| 29407 | 26.8% | $85,367 | $4.05 |
| 29414 | 12.3% | $99,529 | $2.99 |
| 29401 | 9.4% | $99,667 | $4.05 |
| 29492 | 5.8% | $110,509 | $2.95 |

The two most expensive ZIPs (29401, 29407) are **9.4% and 26.8% Black with the highest incomes in the set**. The most heavily Black ZIP (29405, 54%) sits at the low price. Correlation with Black share is **-0.225** (negative); with income it is **+0.236** (positive). Directionally this is a higher-income premium, not a race penalty — though with six ZIPs and three price points, neither is statistically meaningful on its own.

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