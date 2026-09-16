# Income, not race, predicts rural milk prices

**On 1,003 rural ZIP codes carrying both retailers: once income is in the model, race
adds nothing at either chain. Income survives everything — −7.5¢/gallon per $10,000 of
median household income at Walmart, t −4.44, with state fixed effects.**

Reproduce: `python3 analysis/income_race_joint.py`

---

## The setup

1,003 rural ZIPs carry both a Walmart and an Aldi milk price, on identical demographics.
Race and income therefore enter once, and the two retailers are two outcomes measured
over the same geography. Black rural ZIPs (≥30%) are **$18,584 poorer** than non-Black
ones (≤10%) and differ by 42.5 points in Black share.

## 1. Race and income entered together

| Walmart | %Black coefficient | income coefficient |
|---|---|---|
| race alone | +0.00568 (t +1.62) | — |
| + income | **+0.00142 (t +0.40)** | −0.1049 (t −3.55) |
| + income + log population | +0.00206 (t +0.64) | −0.0758 (t −3.26) |
| **+ state fixed effects** | **−0.00050 (t −0.30)** | **−0.0749 (t −4.44)** |

| Aldi | %Black coefficient | income coefficient |
|---|---|---|
| race alone | +0.00357 (t +1.08) | — |
| + income | **+0.00232 (t +0.63)** | −0.0308 (t −2.15) |
| + income + log population | +0.00238 (t +0.64) | −0.0280 (t −1.53) |
| **+ state fixed effects** | **+0.00030 (t +0.09)** | −0.0183 (t −0.93) |

**Race never reaches significance at either retailer, in any specification**, and falls
to essentially zero once income enters. Income is significant at Walmart throughout and
strengthens under state fixed effects.

## 2. Decomposing the raw gap

| | raw gap | attributable to income | attributable to race | residual (absorbed by state) |
|---|---|---|---|---|
| **Walmart** | **+$0.269** | **+$0.139** | −$0.021 | +$0.151 |
| **Aldi** | **+$0.174** | +$0.034 | +$0.013 | +$0.127 |

At Walmart, roughly **half** the observed Black/non-Black price gap is the income
difference between those ZIPs, essentially none is race, and the remainder is which
state the ZIPs are in. At Aldi income explains less and state composition more.

Indicative rather than exact: it applies linear coefficients to a difference in means.

## 3. State by state, race controlling for income

| state | n | Walmart %Black | Aldi %Black | Walmart income | same sign |
|---|---|---|---|---|---|
| Alabama | 90 | −0.00683 | −0.00461 | −0.2003 | yes |
| Arkansas | 76 | +0.00511 | −0.00453 | −0.1338 | NO |
| California | 76 | +0.00393 | +0.03440 | −0.0087 | yes |
| Georgia | 94 | −0.00414 | −0.00355 | −0.1430 | yes |
| Louisiana | 69 | +0.00398 | +0.02325 | +0.0157 | yes |
| Mississippi | 61 | −0.00009 | −0.00578 | −0.1301 | yes |
| North Carolina | 122 | −0.01153 | −0.00948 | −0.1499 | yes |
| New York | 60 | +0.01066 | −0.00231 | −0.0247 | NO |
| South Carolina | 59 | +0.00044 | −0.00056 | −0.0987 | NO |
| Tennessee | 89 | +0.00666 | +0.00199 | −0.2291 | yes |
| Texas | 207 | −0.00747 | +0.01992 | −0.0959 | NO |

Race coefficients are small, mixed in sign, and agree between the retailers in 7 of 11
states. **The income coefficient is negative in 10 of 11**, and large where it is
negative — Tennessee −23¢, Alabama −20¢ per $10,000.

## 4. The finding worth keeping

**Rural milk is priced regressively in income.** At Walmart, each $10,000 of additional
median household income is associated with **7.5¢ a gallon less**, holding state and
population constant, t −4.44. Poorer rural communities pay more for the same gallon of
store-brand milk.

Three things make this the most durable result in the retail strand:

- **It does not depend on racial classification at all**, so it sidesteps the threshold
  and composition problems that have destabilised every racial estimate in this project.
- **Income is measured directly** rather than proxied, and the confound runs *toward* the
  finding rather than away: one would expect discount-format competition to make poorer
  areas cheaper, not dearer.
- **It survives state fixed effects and strengthens under them**, so it is a within-state
  relationship, not the between-state composition effect that has undone the racial
  results.

**At Aldi the same sign appears but does not survive** (−0.0183, t −0.93 with state fixed
effects), so this should be stated as a Walmart finding with Aldi as weak corroboration,
not as a market-wide regularity.

## 5. What this does to the racial claim

It does not refute the incidence. Black rural Americans do pay more for milk — the raw
gap is +27¢ at Walmart, and the earlier descriptive table shows it at both retailers in
7 of 9 states. What the joint model shows is **why**: they live in poorer communities,
and poorer rural communities pay more, in states that are more expensive.

That is still a disparity with a racial incidence. It is not a racial gradient in
pricing, and the two should not be described interchangeably. A memorandum that says
"milk costs more in Black rural communities" is supported; one that says "price rises
with the Black share of a community" is not, once income is in the model.

## 6. Coverage note

Aldi is the only second retailer reachable. Probing the Instacart white-label pattern
that makes aldi.us collectable found no equivalent at Food Lion, Publix, Harris Teeter,
Dollar General, Save A Lot, Sprouts, Winn-Dixie, Piggly Wiggly, Family Dollar, Ingles or
Brookshire's — the last links to Instacart in its footer but runs no storefront. Existing
Harris Teeter (26 ZIPs), Lidl (7) and Dollar General (8) collections are far too thin for
a state panel.
