# Aldi as a control: the same design, a different chain, the opposite sign

**In the exact segment where Walmart's racial gradient appears, Aldi's runs the other
way — measured on the same ZIP codes. The retailer difference is 24¢/gallon. It is
directionally clear and it is not statistically significant.**

Reproduce: `python3 analysis/aldi_comparison.py`

---

## Why this is the test that matters

`reports/segmented_rural.md` finds a racial gradient in Walmart milk prices confined to
low-income rural areas: +19¢/gallon raw, +8.5¢ within state. The obvious objection is
that this is not Walmart — it is the rural South. High-Black rural ZIPs sit in the
Delta and Black Belt, low-Black rural ZIPs sit in the Ozarks and Appalachia, and those
are different markets with different freight, competition and demand.

**Aldi separates those two explanations.** A different chain, a different pricing
architecture, the same ZIP codes. If the gradient is the rural South, Aldi should show
it too. If it is the retailer, Aldi should not.

## 1. Two objections cleared first

**Is the Aldi panel just South Carolina?** No. The low-income rural cell is
NC 38, AR 38, LA 36, GA 35, MS 32, TN 30, AL 28, TX 27 — spread across exactly the
states where Walmart's gradient lives.

**Are these the same places?** Yes. **1,333 ZIP codes carry both an Aldi and a Walmart
price**, across 12 states, joined to one demographic source so the covariates are
identical by construction.

## 2. The headline: the same 295 ZIPs, both retailers

Low-income rural cell, 138 ZIPs ≥30% Black against 75 ZIPs ≤10% Black:

| retailer | high-Black | low-Black | gap |
|---|---|---|---|
| **Walmart** | $4.094 | $3.954 | **+$0.139** |
| **Aldi** | $3.127 | $3.232 | **−$0.105** |
| **difference** | | | **+$0.244** |

Walmart charges more in the Blacker ZIPs. **Aldi, in those same ZIPs, charges less.**

Equivalently: Walmart's premium over Aldi is **+$0.967** in the high-Black ZIPs and
**+$0.722** in the low-Black ones — a 24¢ wider gap where more Black residents live.

Regression on the same ZIPs, controlling income and log population:

| | coef $/gal per point | t conventional | t clustered on state |
|---|---|---|---|
| Walmart | +0.00175 | +1.09 | +0.72 |
| Aldi | −0.00318 | −1.43 | −0.78 |
| **Walmart − Aldi** | **+0.00493** | **+1.88** | **+0.96** |

Differencing the two retailers at the same ZIP removes everything common to the
location — freight, local demand, competition, income, urbanicity, the Class I
differential. **What is left is the retailer.** This is the cleanest identification the
available data supports, and it is why this design is worth more than any single-chain
regression in this project.

**It is also not significant.** With 12 state clusters, t = +0.96. The conventional
t of +1.88 is the one that ignores clustering, and it should not be quoted alone.

## 3. Aldi on its own terms

Pooled across all 1,333 ZIPs:

| specification | coef | t naive | t state | t zone |
|---|---|---|---|---|
| %Black alone | −0.00008 | −0.08 | −0.03 | −0.06 |
| + income + urbanicity | −0.00174 | −1.67 | −0.61 | −1.33 |
| + log population | −0.00181 | −1.73 | −0.62 | −1.35 |

Flat to slightly negative throughout. In the low-income rural cell, Aldi under county
fixed effects is **−0.00781 (t −2.08 naive, −3.14 state-clustered, −2.87
zone-clustered)** — significantly *negative*. Wherever Aldi moves, it moves the other
way.

## 4. CORRECTED — the mechanism claim was wrong

**An earlier version of this report claimed that Aldi prices by zone, that every ZIP
inside a zone pays an identical price, and that a racial gradient is therefore close to
arithmetically impossible at Aldi. That is false, and it was published.**

Tested directly against the collection:

| | |
|---|---|
| Zones in the August data | 530 |
| **Zones carrying more than one price** | **172 (32%)** |
| ZIPs sitting in a multi-price zone | **1,128 of 1,886** |
| Largest within-zone spread | **$2.56** |

The live storefront shows why. ZIPs **29201** and **29063** share **zoneId 348** but
resolve to **shopId 16596** and **shopId 408312**, and to **$2.85** and **$5.85**. Both
are genuine Aldi (retailer slug `aldi`, store configuration `aldi-us-sfp`). **The zone
field is a service and delivery zone. The pricing unit is the shop**, which the August
collection did not capture.

The zone-price-on-%Black statistic previously reported (+0.0039/pt, t +1.16) took one
price per zone and is therefore mis-specified. It is withdrawn.

### What is true instead — and it is a better comparison

The two chains disperse **almost identically**:

| | distinct prices nationally | median per state | sd |
|---|---|---|---|
| Aldi (1,333 ZIPs, 12 states) | 63 | **21** | **$0.597** |
| Walmart (3,768 ZIPs, 43 states) | 177 | **21** | **$0.588** |

Aldi varies its milk price store by store just as freely as Walmart does. So the
retailer difference in §2 cannot be explained by one chain being structurally unable to
price on geography — **both can, and they still move in opposite directions on racial
composition.** That is a stronger comparison than the architectural story it replaces,
because it removes a competing explanation rather than relying on one.

**What is unaffected:** the matched-ZIP comparison in §2 never used the zone field. The
+$0.244 difference, and the regressions behind it, stand exactly as reported. Only
the zone-clustered standard errors have been removed from `analysis/aldi_comparison.py`,
since they clustered on a unit that does not set price; state clustering is retained and
is what the significance statements rest on.

**Also unaffected:** the Walmart milk carve-out (`reports/walmart_basket_national.md`)
is a comparison *across products within Walmart* — milk taking 17–25 prices while
mozzarella and canned green beans take one. Nothing here bears on it.

## 5. What this does and does not support

**Supports:** the rural gradient is not simply "the rural South." The same ZIP codes,
same demographics, same design, produce a positive gap at Walmart and a negative one at
Aldi — and, per §4, not because Aldi is structurally unable to do otherwise. Whatever
drives it is not a location factor common to both retailers.

**Does not support:** a statistically demonstrated difference. The difference-in-
differences is +24¢ with t = +0.96 clustered. Nor does it support any claim about
conduct, intent or policy. And it no longer supports any argument from pricing
architecture — see §4.

**The assumption the design rests on,** which should be stated whenever it is used:
absent any racial gradient, the Walmart-minus-Aldi spread would be constant across
ZIPs. The two chains price different private labels at different levels — Aldi is a
discounter, and the average spread is 72¢–97¢ — so the *level* of that spread carries no
meaning. Only its variation with racial composition does.

## 6. Limits

- **12 state clusters.** This is the binding constraint on every significance test here.
- **Aldi coverage is uneven** — TX 336 ZIPs, CA 189, then NC, GA, AL, SC, TN, AR. The
  low-income rural cell is better balanced than the panel as a whole.
- **Single snapshot, same pipeline.** Both series come from the collection this project
  has not been able to reproduce independently (`reports/brightdata_zipcode_trap.md` §9).
  A sourcing failure would affect both retailers, though not necessarily equally.
- **Product comparability.** Walmart Great Value whole gallon against Aldi's own-label
  whole gallon. Comparable in category, not identical goods.
