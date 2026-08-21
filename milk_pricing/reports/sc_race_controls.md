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
