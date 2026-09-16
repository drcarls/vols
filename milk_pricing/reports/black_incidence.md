# Who bears the gradient: counting people, not ZIPs

`analysis/black_incidence.py` · rural Walmart panel, 2,248 ZIPs, 42 states,
5.53M Black and 36.45M white residents.

## The point being tested

You do not need a race-based pricing rule to have a disparate-impact claim. You
need a facially neutral practice whose burden falls unequally. Walmart's rural
price falls 75¢/gal from the poorest rural income decile to the richest; Black
rural residents are concentrated in the poorest deciles; therefore they bear more
of it. That is a coherent claim and the ZIP-level "race coefficient is zero"
result does not answer it — it answers a different question.

But the claim has to be quantified in the right unit, and doing so changes the
headline number a great deal.

## 1. The person-weighted gap is 6.6¢, not 32¢

Each ZIP contributes pop × %Black Black residents and pop × %White white
residents, each facing that ZIP's posted price.

| | Black | white | gap |
|---|---|---|---|
| as posted | **3.586** | **3.519** | **+0.066** |
| income equalised (by decile) | 3.533 | 3.559 | −0.026 |

**This is the number that belongs in a memo about families, and it is a fifth of
the ZIP-level figure.** The 32¢ headline compares the 79 majority-Black rural ZIPs
against the 1,892 majority-white ones. Most Black rural residents do not live in a
majority-Black ZIP; the average Black rural resident lives in a ZIP that is a
minority Black, at a price much closer to the white average. Person-weighting also
gives no extra weight to the small, extreme, high-price ZIPs that drive the
community-level contrast.

Both statistics are legitimate and they answer different questions:

- **+32¢ (ZIP-level, extreme contrast)** — what do the most heavily Black rural
  communities pay against the whitest ones? Right for "are Black *communities*
  differently situated".
- **+6.6¢ (person-weighted)** — what does the average Black rural resident pay
  against the average white one? Right for "what does this *cost Black families*".

Quoting the first while arguing the second is the error opposing counsel will
find first. Of the 6.6¢, 9.3¢ is attributable to the price-income gradient and
−2.6¢ to everything else — i.e. the gradient accounts for more than the whole gap.

## 2. Exposure, person-weighted

| decile | income from | mean price | % of Black rural residents | % of white rural residents |
|---|---|---|---|---|
| 1 | $22,221 | **4.000** | **20.1%** | 5.6% |
| 2 | $45,516 | 3.866 | 11.7% | 8.0% |
| 3 | $50,627 | 3.729 | 9.5% | 8.4% |
| 4 | $54,351 | 3.740 | 8.5% | 8.9% |
| 5 | $58,204 | 3.676 | 8.0% | 10.5% |
| 6 | $61,780 | 3.464 | 8.9% | 10.7% |
| 7 | $65,937 | 3.564 | 8.7% | 10.7% |
| 8 | $71,300 | 3.497 | 9.2% | 11.6% |
| 9 | $79,669 | 3.414 | 8.3% | 12.6% |
| 10 | $93,452 | 3.392 | 7.2% | 13.1% |

31.8% of Black rural residents against 13.6% of white rural residents sit in the
bottom two income deciles — a 2.3× over-representation where milk is most
expensive. Note this is 2.3×, not the 4.2× the ZIP-level table shows, for the same
reason as above.

The white distribution tilts gently upward (5.6% → 13.1%); the Black distribution
is front-loaded (20.1% in decile 1). The unequal burden is real and visible here.
It is simply smaller than the ZIP-count version implies.

## 3. The gradient is the whole mechanism

On the 1,003 rural ZIPs carrying both retailers, the price–income slope is
−0.1095/gal per $10,000 at Walmart and −0.0383 at Aldi. Give Walmart Aldi's slope
while holding its average price level fixed:

| | Black | white | gap |
|---|---|---|---|
| Walmart as posted | 3.659 | 3.596 | +0.063 |
| Walmart at Aldi's slope | 3.636 | 3.633 | **+0.003** |

**Flattening the gradient to a competitor's — with no reduction in Walmart's
average price — removes 96% of the Black/white incidence.** Nothing about the
demographics changes; only the slope does. This is as clean a demonstration as
this data can give that the incidence is produced by the pricing gradient and not
by geography, freight, or store mix.

It is also the most useful exhibit for a causation argument, because the
counterfactual is not hypothetical: a competitor operating the same rural ZIPs
already prices that way.

## 4. What it costs, on milk

| | per person/yr | aggregate |
|---|---|---|
| as posted, vs white rural residents | $1.13 | $6.2M/yr |
| attributable to the income gradient | $1.57 | $8.7M/yr |

At 17 gal/person/yr (USDA ERS per-capita fluid milk availability) across 5.53M
Black rural residents.

**This is a small number and should be presented as one.** A dollar a year on milk
is not a damages case. What it is, is a *measurement* of one item in a basket,
chosen because milk has a federal regulatory price component that made it
tractable. The finding that matters is the gradient itself — 75¢/gal across the
rural income distribution, 96% of the incidence removable by flattening it — and
the open question is whether the same gradient runs through the rest of the
basket. If it does, the per-household number is one or two orders of magnitude
larger. If it does not, milk is idiosyncratic and this is not a case.

## What to do next

The basket data on hand (`data/walmart_basket_national.csv`, 248 rows) is far too
small to test this. The single highest-value collection now is a **multi-item
basket at the same rural store set** — the ~2,248 rural stores already identified,
priced across 15–25 staples — run through the identical income-decile design. That
converts "milk costs $1.13/yr more" into a grocery-bill figure, and it is the
difference between an interesting pricing finding and an actionable one.

Everything needed to run it exists: the store list, the demographics, the decile
design, and the Aldi counterfactual.
