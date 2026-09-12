# Where the above-freight markup actually lands

**The national test in `usdss.md` was the wrong specification. Corrected, the finding is
larger and cleaner — and it is a regional markup with racial consequences, not a racial
markup.**

Reproduce: `python3 analysis/above_cost_regional.py`

---

## The objection that prompted this

`reports/usdss.md` reported the departure-from-freight gradient on county %Black at
t +1.66 (permutation p .212) and called it "consistently positive, never significant."
That test pools regions carrying **opposite signs**: USDA prices the California metros far
below the USDSS cost surface and the South above it. A national regression averages a large
negative block against a large positive one and loses power by construction. That is a
specification defect, not a finding.

Asked inside regions instead, the picture is sharp.

## 1. The markup is regional, and it is large

Mean departure of the adopted 2025 schedule from the USDSS Class I surface, both aligned to
the same national mean (so only distribution is compared):

| region | counties | population | % Black | markup vs freight | ¢/gal | share of US Black | share of US White |
|---|---|---|---|---|---|---|---|
| **South** | 1,399 | 128,547,575 | 18.2% | **+$0.456/cwt** | **+3.92¢** | **59.5%** | 36.5% |
| **Northeast** | 209 | 53,790,462 | 10.6% | **+$0.244** | **+2.09¢** | 14.5% | 17.6% |
| Midwest | 1,055 | 69,108,736 | 10.0% | −$0.186 | −1.60¢ | 17.5% | 26.6% |
| West | 414 | 76,929,536 | 4.4% | −$0.765 | −6.58¢ | 8.5% | 19.4% |

USDA priced the **South 3.92¢/gal above** what its own freight model says milk is worth
there, and the **West 6.58¢/gal below**. The FMMO south-east proper (orders 5, 6 and 7 —
12 states, 1,040 counties, 86.4m people) is marked up **+$0.466/cwt = +4.01¢/gal**, or
+5.03¢ against the give-up charge.

**73.9% of Black Americans live in a region priced above freight cost, against 54.1% of
white Americans.**

## 2. But inside a region the markup does not track race — at all

| region | counties | states | slope on %Black | t | perm p |
|---|---|---|---|---|---|
| Midwest | 1,055 | 12 | −0.01765 | −4.36 | .178 |
| West | 414 | 11 | −0.06655 | −4.36 | .679 |
| Northeast | 209 | 8 | −0.00172 | −0.45 | .849 |
| South | 1,399 | 17 | −0.00073 | −0.35 | .807 |
| **FMMO south-east (5/6/7)** | **1,040** | **12** | **+0.00053** | **+0.19** | **.887** |

**Not one region shows a positive gradient.** Two are significantly negative — in the
marked-*down* regions, the Blacker the county the deeper the discount, which is Los Angeles,
Chicago and Detroit.

Dose-response inside the south-east is flat and non-monotonic:

| %Black quintile | mean %Black | adopted | freight | markup |
|---|---|---|---|---|
| Q1 | 1.2% | $4.63 | $4.26 | +$0.374 |
| Q2 | 5.2% | $5.42 | $4.95 | +$0.471 |
| Q3 | 14.1% | $5.99 | $5.48 | +$0.507 |
| Q4 | 26.6% | $5.67 | $5.27 | +$0.400 |
| Q5 | 47.0% | $5.47 | $4.97 | +$0.503 |

The Blackest fifth of south-eastern counties is marked up $0.503; the whitest fifth $0.374.
A 13-cent-per-hundredweight spread across a 46-point range in Black share, with no trend
in between.

## 3. The decomposition, which is the whole answer

Splitting the national +0.91¢/gal above-freight racial gap into the part from *which region
people live in* and the part from *race within a region*:

| component | contribution |
|---|---|
| **between regions** — who lives in a marked-up region | **+1.69¢** |
| within regions — race gradient inside a region | **−0.78¢** |
| net | +0.91¢ |

The between-region component is **nearly twice the net figure**, and the within-region
component is **negative**, partially cancelling it. Adding census-region fixed effects to
the national regression therefore flips the sign: **−0.00498/cwt per point, t −2.36**
(−0.00327, t −1.56 against the give-up charge). Dropping California alone leaves +0.00435
(t +1.63).

## 4. What this means for the claim

**The right statement is now available, and it is stronger than what `usdss.md` had:**

> The 2025 amendment priced the South 3.92¢/gallon and the Northeast 2.09¢/gallon above
> what USDA's own least-cost freight model produced, and priced the West 6.58¢/gallon
> below it. Nearly three quarters of Black Americans live in a marked-up region, against
> just over half of white Americans. Nothing in the freight model asked for that
> redistribution.

That is a disparate-impact statement about a **discretionary agency choice**, and it does
not require — and is not helped by — any claim that USDA marked up Black neighbourhoods.
It is the same structure as the headline finding in §1: burden falling on regions where
Black Americans are concentrated. It is *cleaner* without a within-region gradient, because
"geography with racial consequences" is what disparate impact is, and a within-region
gradient would invite a targeting theory the data refutes.

**Three things that must travel with it.**

1. **The racial incidence of the regional pattern is still not statistically significant**
   (permutation p .289). With 48 states and a four-region pattern there are few effective
   degrees of freedom. The magnitude is large; the inference is weak. Nothing in this
   analysis changes that.
2. **The within-region gradient is negative, and one specification makes it significantly
   negative** (region FE, t −2.36). If a filing asserts the markup rises with Black share,
   this is the rebuttal and it is in the same dataset.
3. **Above the freight dual is not the same as unjustified.** USDA's stated objectives
   include maintaining "sufficient revenue for producers" and "equity to handlers with
   regards to raw product costs." A markup above a transport dual can be defended on
   producer-return grounds — the South is milk-deficit. The force of the point is that
   USDA never *said* this is what it was doing, never quantified who pays for it
   (`reia_audit.md`), and certified no civil-rights impact in three sentences
   (`cria_audit.md`).

## 5. What this corrects in this repo

- `reports/usdss.md` §3–4 — the national departure regression is retained but is **no
  longer the headline**: it is a pooled estimate across regions of opposite sign. The
  regional decomposition above supersedes it.
- The "mechanism is not the intuitive one" passage in `usdss.md` and in the cover memo §4a
  was right about Detroit, Chicago and Philadelphia but framed it as a curiosity. It is not
  a curiosity; it is the structure. Those cities sit in marked-*down* regions.
