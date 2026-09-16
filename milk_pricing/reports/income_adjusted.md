# Milk price by racial composition, holding income equal

`analysis/income_adjusted.py` · rural ZIPs. Full Walmart panel: 2,248 ZIPs, 42
states. Both-retailer subsample: 1,003 ZIPs, 11 states.

## The question

Rural Black ZIPs pay 28–32¢/gal more at Walmart than rural white ZIPs, and they
are also ~$18,600 poorer in a market where poorer rural areas pay more (−7.9¢/gal
per $10,000). This asks the counterfactual directly: **set every ZIP to the same
income and what is left?**

## 1. Rural Walmart prices, raw and income-equalised

Both adjusted columns put every group at the sample-average income of $66,084, so
all three columns are on the price scale and directly comparable.

| group | n | actual income | raw | income-adjusted (linear) | income-adjusted (by decile) |
|---|---|---|---|---|---|
| ≥50% Black | 79 | $47,013 | **3.932** | 3.781 | **3.698** |
| 30–50% Black | 156 | $51,466 | 3.847 | 3.732 | 3.679 |
| 10–30% Black | 427 | $65,120 | 3.643 | 3.636 | 3.636 |
| ≤10% Black | 1,591 | $68,699 | **3.596** | 3.617 | **3.626** |
| **top-to-bottom spread** | | | **+0.336** | +0.164 | **+0.072** |

The ordering survives — the gradient is still monotone in Black share after income
is equalised — but the magnitude does not. A 33.6¢ spread becomes 7.2¢.

## 2. Four ways of equalising income, ≥30% vs ≤10% Black

| method | Walmart (full panel) | Walmart (both-retailer) | Aldi |
|---|---|---|---|
| raw, no adjustment | +0.280 | +0.269 | +0.174 |
| 1. linear income adjustment | +0.131 | +0.066 | +0.103 |
| 2. within income decile | **+0.043** | +0.012 | +0.190 |
| 3. matched on income ±$2,000 | **+0.039** | −0.010 | +0.229 |
| 4. linear income + state FE | −0.021 | −0.024 | +0.023 |

Clustered on state, the decile-adjusted Walmart gap is +0.059 (t +0.37) on the
full panel and +0.007 (t +0.04) on the both-retailer sample. Neither is
distinguishable from zero. Match quality is not the issue: 235 of 235 high-Black
ZIPs found a low-Black ZIP inside a $2,000 income caliper.

**The linear adjustment under-controls.** It leaves +13.1¢ where the two
nonparametric methods leave +4¢. That gap between methods is itself a finding: the
price–income relationship is steeper at the bottom of the income distribution than
a single slope allows, so fitting one line and calling income controlled leaves
part of the income effect sitting in the race coefficient. Anyone replicating this
with a plain OLS income control will get the larger, more favourable number for
the wrong reason.

## 3. Within-decile detail, Walmart full panel

| decile | income from | n ≥30% Black | n ≤10% Black | gap |
|---|---|---|---|---|
| 1 | $22,221 | 100 | 84 | +0.153 |
| 2 | $45,516 | 40 | 131 | +0.234 |
| 3 | $50,627 | 23 | 156 | −0.167 |
| 4 | $54,351 | 19 | 175 | −0.061 |
| 5 | $58,204 | 12 | 169 | +0.317 |
| 6 | $61,780 | 12 | 172 | −0.101 |
| 7 | $65,937 | 12 | 169 | +0.063 |
| 8 | $71,300 | 10 | 168 | +0.210 |
| 9 | $79,669 | 5 | 176 | −0.246 |
| 10 | $93,452 | 2 | 191 | too few |

Five of nine deciles positive, signs alternating, individual deciles running from
−25¢ to +32¢. Above decile 2 there are rarely more than a dozen high-Black rural
ZIPs to compare, which is why the pooled estimate is weighted toward the bottom
two deciles — and those two are the positive ones (+0.153, +0.234). The pooled
+0.043 is not being driven by a handful of thin cells; it is a small positive
number in the cells that have data and noise elsewhere.

## 4. Aldi does not follow Walmart here

Aldi's income slope is −0.038/gal per $10,000, less than half Walmart's −0.110 on
the same ZIPs. Because income barely predicts Aldi's price, equalising income
barely moves Aldi's racial gap: +0.174 raw becomes +0.190 by decile and +0.229
matched. On its face that is a racial gap that income does *not* explain.

Three reasons not to lead with it:

1. **State fixed effects collapse it** to +0.023. Walmart's holds a consistent
   near-zero across specifications; Aldi's does not.
2. **It is definition-unstable.** Majority Black vs majority white at Aldi is
   +0.0¢ (reports/rural_price_by_state.csv); ≥30% vs ≤10% is +17.4¢ raw. A result
   that swings 17¢ on where a threshold is drawn is a result about the threshold.
3. **Aldi's price is non-monotone in Black share.** The ≤10% Black group is the
   cheapest at $2.936 but the 10–30% group is the *most expensive* at $3.146,
   above both Black-majority groups. That is not a racial gradient; it is Aldi's
   store footprint.

Aldi should be reported as what it is — a second retailer over the same geography
whose racial gap is smaller than Walmart's raw gap, sensitive to specification,
and not monotone — rather than as a comparison that either confirms or refutes
Walmart.

## What to say

> Rural ZIPs that are majority Black pay $3.93/gal at Walmart; rural ZIPs under
> 10% Black pay $3.60. Set both to the same income and the prices are $3.70 and
> $3.63 — a 7¢ difference that is not statistically distinguishable from zero.
> Income, not race, is what predicts the rural Walmart price: 7.9¢/gal for every
> $10,000 of median household income, and more steeply than that at the bottom of
> the distribution.

The disparate-impact argument that survives this is about income and rural
geography, and about the fact that Black rural households are concentrated in the
poorest rural income deciles. It is not a claim that Walmart prices by race.
