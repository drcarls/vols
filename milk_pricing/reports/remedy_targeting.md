# "Walmart could lower its price in high-Black rural areas"

`analysis/remedy_targeting.py` · rural panel, 2,248 ZIPs, 5.53M Black residents.

## The reading this corrects

The Aldi-slope counterfactual is naturally read as *Walmart could charge less in
high-Black rural areas*. That is not what it does. It flattens the price–**income**
gradient. The benefit lands disproportionately on Black areas because Black rural
residents are concentrated at the bottom of the rural income distribution — race
never enters the rule. The distinction is not pedantic:

- **Legally**, asking a retailer to condition price on the racial composition of a
  ZIP is a different request from asking it not to condition price on income, and
  a much harder one to put in a consent decree.
- **Empirically**, the two policies reach different people, and the race-targeted
  one reaches far fewer Black families than it sounds like it should.

## 1. Most Black rural residents do not live in a majority-Black ZIP

| target set | ZIPs | % of Black rural residents | mean price |
|---|---|---|---|
| majority-Black ZIPs | 79 | **19.5%** | 3.932 |
| ≥30% Black ZIPs | 235 | 45.2% | 3.876 |
| ≥20% Black ZIPs | 371 | 60.5% | 3.814 |
| bottom two income deciles | 450 | **31.8%** | 3.933 |
| bottom three income deciles | 675 | 41.3% | 3.865 |

A cut aimed at majority-Black ZIPs reaches **19.5%** of Black rural residents. A
cut aimed at the bottom two income deciles reaches **31.8%** — more Black families,
at almost exactly the same mean price ($3.933 vs $3.932), using a rule that never
mentions race.

## 2. The two policies, scored

'Disparity' is Black minus white — the part of the benefit *not* also delivered to
white rural residents. It is the only column that measures a remedy rather than a
price cut.

| policy | Black | white | disparity | $/yr | gap closed |
|---|---|---|---|---|---|
| cut majority-Black ZIPs to the majority-white mean | −0.7¢ | −0.1¢ | **−0.6¢** | −$0.10 | **9%** |
| flatten the income gradient to Aldi's slope | −1.8¢ | +1.6¢ | −3.4¢ | −$0.58 | 51% |
| cap every rural ZIP at the mean-income fitted price | −26.7¢ | −18.9¢ | **−7.9¢** | −$1.34 | 118% |

The race-targeted policy is the *weakest* of the three. It closes 9% of the
person-weighted gap because four-fifths of Black rural residents live outside the
ZIPs it touches. The income-targeted policies close 51% and 118% while never
referring to race.

**Correction to carry forward.** The 96% figure in `reports/black_incidence.md` §3
is on the 1,003 ZIPs where both Walmart and Aldi operate — the right sample for a
Walmart-vs-Aldi comparison, and a sample that is 17.1% Black against 4.2% for the
rural ZIPs Aldi does not serve. Applied to the full 2,248-ZIP rural panel, the
same flattening closes **51%**, not 96%. Both are correct for their sample; 51% is
the number for a claim about rural America, and it is the one to quote.

## 3. Is the lower price observed anywhere?

| | price |
|---|---|
| Walmart, bottom two rural income deciles | 3.933 |
| Walmart, top two rural income deciles | 3.403 |
| Aldi, the same bottom-two-decile ZIPs | 3.087 |

Walmart already charges 53¢ less in richer rural ZIPs, and a competitor charges
85¢ less in these same poor rural ZIPs. That establishes the price point is
**achievable in these markets** — not that it is profitable. No cost, freight, or
margin data is available for either chain, so nothing here supports a claim about
what Walmart could afford.

## What to say

> The finding does not show that Walmart charges more because a rural area is
> Black, and the remedy it points to is not a race-conditioned price. It shows
> that Walmart's rural price rises sharply as local income falls — 75¢/gal across
> the rural income distribution, against 19¢ for a competitor in the same ZIPs —
> and that Black rural residents are 2.3× over-represented in the deciles where
> that gradient bites. Flattening the income gradient, a facially neutral change,
> closes about half the Black/white price disparity in rural America. Targeting
> majority-Black ZIPs directly would close 9% of it, because most Black rural
> families do not live in one.

For a disparate-impact theory this is the stronger posture on both elements: the
challenged practice is neutral on its face (income-graded pricing), its racial
incidence is measurable, and the less-discriminatory alternative is not
hypothetical — a competitor already operates it in the same stores' markets.
