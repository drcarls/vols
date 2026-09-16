# Within state or between states?

`analysis/within_state_gap.py` · 1,003 rural ZIPs carrying both a Walmart and an
Aldi price, 11 states.

## Why this exists

An earlier summary said the part of the rural Black/white price gap that income
does not explain is "mostly which state you are in." That was imprecise, and in
one reading it was wrong. It conflates two separate claims:

- **(a)** Black rural ZIPs sit disproportionately in states where rural milk is
  expensive for everyone.
- **(b)** Inside a given state, Black and white rural ZIPs pay the same.

(a) is true and is most of the raw gap. (b) is **not** established by the data,
and the descriptive state table contradicts it. State fixed effects absorbing the
residual is evidence for (a); it is not evidence for (b), because the same
absorption happens whether the within-state gradient is zero or merely imprecise.
Here it is the latter.

## 1. The gradient does not vanish inside states

%Black slope in dollars per gallon per percentage point, income excluded, SEs
clustered on state.

| | Walmart | Aldi |
|---|---|---|
| pooled across states | **+0.00568** (t +1.62) | +0.00357 (t +1.08) |
| within state (state FE) | **+0.00224** (t +1.40) | +0.00094 (t +0.32) |

Demeaning by state cuts the Walmart gradient to about 40% of its pooled size —
but it does not zero it, and the t-statistic barely moves, because the standard
error falls along with the point estimate. A 30-point swing in Black share still
moves the within-state Walmart price **+6.7¢/gal** (Aldi +2.8¢). Neither the
pooled nor the within-state slope is significant at 11 state clusters; the honest
statement is that the within-state gradient is positive, roughly a third to a
half the size of the pooled one, and too noisy to separate from zero here.

## 2. State by state, unadjusted

≥30% Black rural ZIPs vs ≤10% Black rural ZIPs, **same state**. States needing at
least five ZIPs on each side.

| st | n hi | n lo | WM hi | WM lo | WM gap | Aldi gap | income gap |
|---|---|---|---|---|---|---|---|
| AL | 24 | 29 | 3.849 | 3.909 | −0.060 | −0.060 | −13,030 |
| AR | 15 | 43 | 4.397 | 3.970 | **+0.426** | −0.437 | −11,409 |
| GA | 41 | 18 | 3.643 | 3.400 | **+0.243** | +0.164 | −15,771 |
| LA | 33 | 6 | 4.634 | 4.528 | +0.106 | +0.113 | −26,271 |
| NC | 26 | 48 | 3.248 | 3.462 | −0.215 | −0.144 | −16,447 |
| SC | 25 | 10 | 3.449 | 3.171 | **+0.278** | +0.045 | −27,408 |
| TN | 6 | 63 | 4.142 | 3.752 | **+0.390** | +0.117 | −11,679 |
| TX | 10 | 140 | 3.594 | 3.613 | −0.019 | +0.534 | −18,195 |

Walmart gap positive in **5 of 8** states, mean +0.144, median +0.174. Aldi
positive in 5 of 8, mean +0.041. Both retailers positive in the same state in 4
of 8. Five of eight is what a coin does; the mean is not, but with this many
states neither settles the question on its own.

Note the income column: in every one of these states the Black rural ZIPs are
between $11k and $27k poorer than the white rural ZIPs in the *same state*. The
income gap is not a between-state artifact either.

## 3. After income

Race and income together, state fixed effects, clustered on state.

| | Walmart | Aldi |
|---|---|---|
| %Black | −0.00127 (t −0.66) | +0.00042 (t +0.13) |
| income per $10k | **−0.09891 (t −4.32)** | −0.01458 (t −0.91) |

Within state, income is what predicts the Walmart price — about 9.9¢/gal per
$10,000 — and once it is in the model the race coefficient is a small negative
with no precision. Income is not a between-state story: the gradient is estimated
entirely off comparisons inside states here.

## 4. Splitting the headline gap

Raw gap uses every ZIP; the within-state column subtracts each state's own mean
price first, restricting to states holding both groups.

| definition | retailer | raw | within-state | between-state | % within |
|---|---|---|---|---|---|
| ≥50% vs ≤10% Black | Walmart | +0.281 | +0.052 | +0.228 | 19% |
| | Aldi | +0.161 | +0.016 | +0.145 | 10% |
| ≥30% vs ≤10% Black | Walmart | +0.269 | **+0.085** | +0.184 | 31% |
| | Aldi | +0.174 | +0.048 | +0.126 | 28% |

So: between-state composition is the larger share — 69% to 90% depending on
definition — but the within-state piece is positive at both retailers under both
definitions, and at the ≥30% definition it is 31% of the Walmart gap, about 8.5¢
per gallon.

## What this changes

The correct characterisation of the rural finding is:

1. Rural Black ZIPs pay 27–32¢/gal more at Walmart than rural white ZIPs.
2. Roughly half of that tracks income, which is the strongest single predictor
   and is itself measured within states.
3. Of the remainder, most — not all — is between-state composition. A positive
   within-state gap survives in the descriptive data (5 of 8 states at Walmart)
   and in the pooled within-state gradient (+6.7¢ per 30 points), but it is not
   statistically distinguishable from zero with 11 state clusters.

Claim (b) above should not be made. "Most of the rest is which state" overstates
what the state fixed effects show; "the gap shrinks by roughly 60–70% when the
comparison is held inside a state, and what remains is positive but imprecise" is
what the data support.
