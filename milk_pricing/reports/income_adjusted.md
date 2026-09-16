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

## 2. Majority Black vs majority white, four ways of equalising income

The definition the cover memo leads with. Full rural Walmart panel: 79
majority-Black ZIPs against 1,892 majority-white ones, a $20,377 income gap.

| method | Walmart (full panel) | Walmart (both-retailer) | Aldi |
|---|---|---|---|
| raw, no adjustment | **+0.321** | +0.223 | +0.000 |
| 1. linear income adjustment | +0.160 | +0.025 | −0.069 |
| 2. within income decile | **+0.060** | −0.018 | −0.032 |
| 3. matched on income ±$2,000 | **+0.050** | −0.065 | −0.210 |
| 4. linear income + state FE | −0.023 | −0.078 | −0.096 |

Decile-adjusted and clustered on state: **+0.070 (t +0.42)**. Same shape as the
30/10 definition and a slightly larger residual — 5–7¢ rather than 4¢ — but on
either definition the adjusted gap is a few cents and nowhere near significant.
All 79 majority-Black ZIPs matched inside the $2,000 caliper.

**The limit of the majority definition.** Holding income equal requires
majority-white ZIPs at the same income *and* majority-Black ZIPs at the same
income, and above the fourth income decile the second condition barely holds:

| decile | income from | n majority Black | n majority white |
|---|---|---|---|
| 1 | $22,221 | 46 | 134 |
| 2 | $45,516 | 9 | 181 |
| 3 | $50,627 | 6 | 186 |
| 4 | $54,351 | 5 | 183 |
| 5–6 | $58,204 | 1, 1 | 201, 208 |
| 7 | $65,937 | 4 | 196 |
| 8 | $71,300 | 5 | 201 |
| 9–10 | $79,669 | 1, 1 | 203, 199 |

Four deciles drop out for want of ZIPs on the Black side. The majority-definition
decile estimate is really deciles 1–4 plus 7–8, weighted heavily toward decile 1.
The 30/10 definition is the better-supported version of the same comparison, which
is why it is the one to put in front of counsel; the majority numbers agree with
it, which is the point of running both.

## 3. Where the two groups actually sit

This is the table that matters, and it is not an adjustment — it is the reason
adjusting changes the answer so much.

| decile | income from | mean rural price | % of majority-Black ZIPs | % of majority-white ZIPs |
|---|---|---|---|---|
| 1 | $22,221 | **4.000** | **58.2%** | 7.1% |
| 2 | $45,516 | 3.866 | 11.4% | 9.6% |
| 3 | $50,627 | 3.729 | 7.6% | 9.8% |
| 4 | $54,351 | 3.740 | 6.3% | 9.7% |
| 5 | $58,204 | 3.676 | 1.3% | 10.6% |
| 6 | $61,780 | 3.464 | 1.3% | 11.0% |
| 7 | $65,937 | 3.564 | 5.1% | 10.4% |
| 8 | $71,300 | 3.497 | 6.3% | 10.6% |
| 9 | $79,669 | 3.414 | 1.3% | 10.7% |
| 10 | $93,452 | 3.392 | 1.3% | 10.5% |

Majority-white rural ZIPs are spread almost uniformly across the income
distribution — 7% to 11% in every decile, which is what "no relationship" looks
like. Majority-Black rural ZIPs are not: **69.6% sit in the bottom two deciles,
against 16.6% of majority-white ones.** Rural milk in those two deciles averages
$3.933 against $3.559 in the other eight.

That is the finding. Not a per-ZIP racial premium — an exposure difference. Black
rural communities are four times as concentrated in the income deciles where rural
milk is most expensive.

## 4. ≥30% vs ≤10% Black, four ways of equalising income

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

## 5. Within-decile detail, Walmart full panel

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

## 6. Aldi, on the same 1,003 rural ZIPs

### The exposure mechanism runs at Walmart and barely at Aldi

Identical ZIPs, identical demographics, two retailers:

| decile | income from | Walmart | Aldi | Walmart − Aldi | % of maj-Black ZIPs | % of maj-white ZIPs |
|---|---|---|---|---|---|---|
| 1 | $23,917 | **4.125** | 3.020 | **1.105** | **50.0%** | 5.9% |
| 2 | $42,885 | 4.102 | 3.155 | 0.947 | 13.5% | 9.0% |
| 3 | $48,013 | 3.905 | 3.036 | 0.869 | 6.8% | 10.2% |
| 4 | $51,626 | 3.835 | 3.116 | 0.719 | 9.5% | 9.4% |
| 5 | $54,955 | 3.786 | 3.101 | 0.684 | 4.1% | 10.7% |
| 6 | $58,865 | 3.715 | 3.071 | 0.644 | 2.7% | 11.6% |
| 7 | $63,306 | 3.556 | 3.010 | 0.547 | 1.4% | 11.3% |
| 8 | $68,770 | 3.496 | 3.123 | 0.374 | 9.5% | 10.3% |
| 9 | $76,990 | 3.535 | 2.909 | 0.626 | 2.7% | 11.3% |
| 10 | $89,434 | **3.375** | 2.826 | **0.549** | 0.0% | 10.3% |

Walmart falls 75¢ from the poorest rural income decile to the richest. Aldi falls
19¢, non-monotonically. The income slopes on these same ZIPs are −0.110/gal per
$10,000 at Walmart and **−0.038 at Aldi**, less than half as steep.

The bottom two deciles hold 63.5% of the majority-Black ZIPs and 14.8% of the
majority-white ones. Milk there costs **+46.3¢** more than the other eight deciles
at Walmart and **+6.3¢** more at Aldi.

**This is the finding that Aldi contributes.** The exposure argument needs two
things: a group concentrated in the low-income deciles, and a price that actually
rises as income falls. The concentration is structural — it is where Black rural
communities are, and it is the same for both retailers by construction. The
gradient is not structural. It is a retailer's pricing decision, and Aldi, serving
the same rural ZIPs, largely does not have one. The Walmart-minus-Aldi spread runs
$1.105 in the poorest rural decile and $0.549 in the richest: Walmart's premium
over Aldi is twice as large where rural Black households are concentrated.

### Aldi's own racial gap is specification-unstable

| method | majority Black vs majority white | ≥30% vs ≤10% Black |
|---|---|---|
| raw | +0.000 | +0.174 |
| linear income adjustment | −0.069 | +0.103 |
| within income decile | −0.032 | +0.190 |
| matched on income ±$2,000 | −0.210 | +0.229 |
| linear income + state FE | −0.096 | +0.023 |

Do not lead with either column. Three reasons:

1. **The two definitions disagree in sign** at every adjustment. A result that
   flips on where a threshold is drawn is a result about the threshold.
2. **Aldi's price is non-monotone in Black share.** The ≤10% Black group is
   cheapest at $2.936, but the 10–30% group is the *most expensive* at $3.146,
   above both Black-majority groups. That is a store-footprint pattern, not a
   racial gradient.
3. **State fixed effects move it a lot** (+0.229 to +0.023 on the 30/10
   definition), where Walmart's near-zero holds across specifications.

The defensible Aldi statement is the flat gradient, not a racial coefficient.

### Coverage

1,003 of 2,248 rural Walmart ZIPs carry an Aldi price (45%).

| | n | mean %Black | majority Black | mean income |
|---|---|---|---|---|
| with Aldi | 1,003 | 17.1 | 7.4% | $63,207 |
| without | 1,245 | 4.2 | 0.4% | $68,401 |

Aldi's rural footprint is not a random sample of rural America — it is four times
Blacker and $5,200 poorer than the rural ZIPs it does not serve, which follows
from Aldi being a Southeast and Midwest chain. This does **not** bias the
Walmart-vs-Aldi contrast, which is run on the shared ZIPs only with Walmart
measured on those same ZIPs. It does mean the Aldi column on its own describes
rural ZIPs Aldi chose to enter, not rural America.

Separately, 398 ZIPs in the Aldi collection have no demographics in the panel
because they carry no Walmart store. Adding ACS data for those would extend the
Aldi-only analysis; it would not change anything above.

## What to say

> Rural ZIPs that are majority Black pay $3.93/gal at Walmart; rural ZIPs that are
> majority white pay $3.61. Set both to the same income and the gap falls to 5-7¢,
> which is not statistically distinguishable from zero. Income, not race, is what
> predicts the rural Walmart price: 7.9¢/gal for every $10,000 of median household
> income, and more steeply than that at the bottom of the distribution.
>
> The disparity is in the exposure, not the per-ZIP price. 69.6% of majority-Black
> rural ZIPs sit in the bottom two income deciles, against 16.6% of majority-white
> ones, and rural milk in those two deciles averages $3.93 against $3.56
> everywhere else.
>
> On the same rural ZIPs, Aldi's price falls 19 cents from the poorest income
> decile to the richest where Walmart's falls 75 cents. The concentration of Black
> rural communities in low-income areas is structural; the price gradient that
> turns it into a cost is a retailer's choice.

The disparate-impact argument that survives this is about income and rural
geography, and about the fact that Black rural households are concentrated in the
poorest rural income deciles. It is not a claim that Walmart prices by race.
