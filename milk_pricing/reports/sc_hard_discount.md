# SC hard discount — complete Aldi sweep and Lidl footprint

## Aldi — every South Carolina ZIP

All **538 SC ZIP codes** were swept against Aldi's Instacart-powered storefront; 50 returned no private-label whole-gallon benchmark, leaving **488 priced ZIPs**.

Whole gallon ranges **$2.19–$4.19**, median **$2.90**.

| Statistic | Value |
|---|---:|
| ZIPs swept | 538 |
| ZIPs priced | 488 |
| Distinct Instacart zoneIds | 29 |
| Min / median / max $/gal | $2.19 / $2.90 / $4.19 |

### zoneId is not the pricing key

The obvious reading of `zoneId` — that it identifies a pricing zone — does not survive the full sweep. ZIPs 29176 and 29402 both report zone 12 and price at **$2.19 and $4.05**, a $1.86 gap, and both are stable on recheck.

An earlier report in this project concluded that Aldi prices whole metros as single flat zones. That was drawn from seven Columbia ZIPs that happened to agree, and the 538-ZIP sweep retires it: price varies within `zoneId` in 22 of the 29 zones observed.

## Lidl — footprint only

**Lidl publishes no online prices.** Every product, search and weekly-ad URL returns an identical 109,918-byte catch-all page; Lidl US runs no grocery e-commerce. The store list is obtainable, the prices are not.

There are **7 Lidl stores in all of South Carolina**:

| ZIP | Location |
|---|---|
| 29072 | Lexington |
| 29118 | Orangeburg |
| 29229 | Columbia (Summit Pkwy) |
| 29420 | North Charleston |
| 29445 | Goose Creek |
| 29707 | Indian Land |
| 29730 | Rock Hill (Herrons Ferry) |

### Lidl is not in the Upstate

The SC footprint is Midlands and Lowcountry only — Columbia, Lexington, Orangeburg, Goose Creek, North Charleston — plus Rock Hill and Indian Land in the Charlotte spillover. **There is no Lidl in Greenville, Spartanburg or Anderson.**

This corrects an earlier claim in this project that the Upstate is where Aldi and Lidl overlap most densely, offered as the explanation for Walmart's lowest SC prices being there (Inman $2.17, Greer $2.36). Lidl is absent from the Upstate entirely, so it cannot be the reason. The `markets.py` note asserting Lidl in Greenville was wrong; the Greenville Lidl link that suggested it is Greenville **NC**, on E Fire Tower Rd.

Whatever holds Walmart's Upstate prices down, it is not Lidl. Aldi's Upstate prices ($2.39 Spartanburg, $2.65 Greenville) are themselves among the lowest in the state, so the more likely reading is that the Upstate is a structurally low-price grocery market rather than one disciplined by a second discounter.

## Limits

- Aldi figures are its Instacart-powered delivered price, which may differ from shelf price.
- 50 ZIPs resolved but carried no private-label whole gallon (assortment or stock), and are excluded rather than imputed.
- Lidl contributes footprint only. Any SC discount-floor estimate that needs Lidl prices is unsupported by this project.