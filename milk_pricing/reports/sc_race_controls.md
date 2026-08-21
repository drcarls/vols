# Does the race effect survive controls in SC?

You asked whether the Black-share effect on Walmart milk price still holds after stripping out income and urbanicity. I had only run one-at-a-time partial correlations and a stratified split, never a joint model — a fair gap, since those can disagree with a full regression. So I fit one.

**It does not hold. But the data also cannot rule it out, and that distinction matters more than the verdict.**

## Nested regressions, n=92

| Model | % Black coef | t | What's significant |
|---|---:|---:|---|
| M1 race alone | +0.0066 | **2.09** | race |
| M2 + income | +0.0034 | 0.81 | nothing |
| **M3 + urbanicity** | **+0.0032** | **0.82** | urban (t=-3.44) |
| M4 + population | +0.0050 | 1.31 | urban, population |
| M5 + Class I diff | +0.0027 | 0.66 | urban, population |

M3 is exactly the specification you described. The race coefficient more than halves from its raw value and lands at **t = 0.82**. What carries the variance is **urbanicity (t = -3.44)** and **population (t = -2.80)**; adding race to a model that already has them improves adjusted R² by essentially nothing.

## It fails in every specification I tried

| Specification | n | coef | t |
|---|---:|---:|---:|
| race + income + urban | 92 | +0.0032 | +0.82 |
| race + income + urban + population | 92 | +0.0050 | +1.31 |
| **rural stores only, + income** | 59 | **+0.0004** | **+0.08** |
| rural only, + income + population | 59 | +0.0020 | +0.39 |
| urban stores only, + income | 33 | -0.0006 | -0.12 |
| log(price) + income + urban | 92 | +0.0010 | +0.83 |
| majority-Black dummy + income + urban | 92 | +0.0277 | +0.16 |
| %Black x rural interaction | 92 | +0.0114 | +1.59 |

The rural-only test is the cleanest, because the rural premium is where any disparity would have to live. Comparing rural stores to rural stores at similar income, the coefficient is **+0.0004 — four ten-thousandths of a cent per percentage point, t = 0.08.** It is not merely insignificant; it is indistinguishable from zero.

The interaction term is the closest anything comes (t = 1.59, p≈0.12), which is worth noting because the sign is positive in *every* specification. Consistent sign with consistent insignificance is what an underpowered true effect looks like — and also what noise looks like.

## Why I won't say the effect is zero

The M3 estimate carries a wide confidence interval:

| | per point of Black share | across a 10%→50% ZIP |
|---|---:|---:|
| point estimate | +0.0032 | **+$0.13/gal** |
| 95% CI low | -0.0046 | -$0.18/gal |
| 95% CI high | +0.0110 | **+$0.44/gal** |

**The data is consistent with anything from an 18-cent discount to a 44-cent premium** on a 40-point swing in Black share. A 44-cent effect would be large and would matter. This sample cannot exclude it.

The reason is collinearity and sample size. In these 92 stores %Black correlates **-0.648** with median income — in rural South Carolina they are close to the same variable, and separating them takes power this sample does not have. Detecting an effect the size of the point estimate at 80% power would need roughly **1,000 stores**.

## What I'd actually conclude

1. **The claim as stated is not supported.** No specification puts the race coefficient near significance, and the one that isolates the rural premium puts it at essentially zero.
2. **The disparate outcome is real regardless.** Walmart's rural premium is large ($3.26 vs $2.72 median) and falls on ZIPs that are poorer and more heavily Black. Whether the mechanism is race or the geography race correlates with, the burden lands the same way.
3. **The mechanism question is unresolved, not resolved.** Anyone claiming either direction from 92 SC stores is over-reading.

## What would settle it

Pool the neighbouring states. SC alone cannot separate race from income and rurality; NC, GA and VA together would give roughly the n needed, and would add ZIPs that break SC's specific race-income collinearity — high-income majority-Black suburbs, low-income majority-white rural areas. That variation is what identifies the coefficient, and South Carolina does not have enough of it.

## Matched pairs

You asked for matched pairs as well. Matching each high-Black store to the nearest low-Black store on income and population within the same geo stratum, greedy nearest-neighbour, no control reused:

| Contrast | Pairs | Mean diff | Median | t | High-Black dearer |
|---|---:|---:|---:|---:|---:|
| ≥40% vs ≤20% Black, ±$10k income, ±15k pop | 7 | +$0.100 | +$0.140 | 0.75 | 5 of 7 |
| ≥35% vs ≤20%, looser calipers | 16 | +$0.186 | +$0.070 | 1.32 | 8 of 16 |
| ≥30% vs ≤25%, loosest | 21 | +$0.271 | +$0.140 | 1.49 | 11 of 21 |

Same pattern as the regressions: **positive every time, significant none of them**, and the win/loss counts are near coin-flips once the sample is big enough to count (8-6, 11-10).

But the matched pairs also show *why*. The matches cross Walmart's price zones — Darlington at $3.82 paired against Oconee at $3.26, different regions entirely. Matching on income and population without matching on geography compares across zones, and the zone is what sets the price.

## The structural answer: price is assigned by zone, and zones are mixed

Walmart's SC prices fall on twelve discrete points. Within any one of them, demographics vary enormously and the price does not vary at all:

| Price | Store-ZIPs | Black share range | Income range |
|---|---:|---|---|
| $3.82 | 15 | **5.1% – 55.7%** | $39.6k – $82.6k |
| $2.50 | 10 | 6.8% – 28.2% | $45.3k – $104.2k |
| $2.72 | 9 | **6.5% – 81.2%** | $39.0k – $100.8k |
| $3.86 | 9 | 9.8% – 46.1% | $42.0k – $95.6k |
| $2.88 | 7 | 1.6% – 41.9% | $30.0k – $71.4k |

Inside the $3.82 zone, Darlington (**55.7% Black, $39.6k income**) and Pickens (**5.1% Black, $63.4k**) pay **exactly the same price**. All fifteen are rural. Inside the $2.72 zone the Black share runs from 6.5% to 81.2% at one price.

That is the mechanism. Walmart sets a price per zone; zones are geographic and demographically heterogeneous. The raw race correlation comes entirely from *which zones* are dearer — rural ones — not from any differentiation within a zone. There is no pricing lever here that could act on race even in principle, because the unit of pricing is a region containing both 5% and 56% Black ZIPs.
