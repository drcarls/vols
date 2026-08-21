# SC Walmart milk — 92 stores vs Aldi, and what drives the price

Source: your `SC_walmart_milk_by_store_zip.csv` (92 store-ZIPs, whole milk, with county, rural/urban, ACS demographics and the Class I differential), joined to this project's 488-ZIP Aldi sweep.

## First: my sampled Walmart data was wrong, twice

Checked store-by-store against your file, the seven stores I collected by random-exit sampling failed in two systematic ways:

| Store | My ZIP | My $ | Real ZIP | Real $ | Δ |
|---|---|---:|---|---:|---:|
| 2806 | 29349 | $2.17 | **29316** | $2.32 | -0.15 |
| 4583 | 29650 | $2.36 | **29615** | $2.50 | -0.14 |
| 630 | 29501 | $2.67 | 29501 | $2.82 | -0.15 |
| 586 | 29526 | $2.74 | 29526 | $2.88 | -0.14 |
| 2712 | 29579 | $2.74 | **29577** | $2.88 | -0.14 |
| 4443 | 29627 | $2.74 | **29621** | $2.88 | -0.14 |
| 795 | 29853 | $3.72 | **29812** | $3.86 | -0.14 |

**The ZIP was wrong in five of seven.** I was recording the proxy exit's postal code, not the store's, so every demographic join on Walmart data was against the wrong ZIP. The store I called "Williston 29853" is Barnwell 29812.

**And every price was low by $0.14–$0.15** — a near-constant offset, so a systematic capture error, not noise. Whatever field I read was not the shelf price your file records.

Everything below uses your data.

## The answer: Walmart runs a rural premium; Aldi does not

Across 84 ZIPs where both are priced:

| | n | Walmart median | Aldi median | Walmart's mean gap |
|---|---:|---:|---:|---:|
| Urban | 30 | $2.72 | $2.85 | **-0.07** |
| Rural | 54 | $3.26 | $2.95 | **+0.21** |

That is the whole story. **In urban SC, Walmart is at or below Aldi. In rural SC, Walmart sits 21 cents above it on average — and Aldi barely moves.** Walmart's rural median is $3.26 against $2.72 urban, a 54-cent step, while Aldi's rural and urban medians differ by ten cents.

The widest reversals are all rural:

| ZIP | County | Walmart | Aldi | Gap |
|---|---|---:|---:|---:|
| 29102 | Clarendon | $4.00 | $2.45 | **+1.55** |
| 29671 | Pickens | $3.82 | $2.65 | **+1.17** |
| 29070 | Lexington | $3.82 | $2.85 | **+0.97** |
| 29108 | Newberry | $3.82 | $2.85 | **+0.97** |
| 29710 | York | $3.82 | $2.89 | **+0.93** |
| 29574 | Dillon | $3.97 | $3.05 | **+0.92** |
| 29379 | Union | $3.82 | $2.90 | **+0.92** |
| 29414 | Charleston | $3.86 | $2.99 | **+0.87** |

Walmart's price ladder is discrete — $2.32, $2.50, $2.72, $2.88, $3.26, $3.82, $3.86 — and the rural stores sit on the $3.82/$3.86 rungs while urban stores sit on $2.50–$2.88. This is zone assignment, not drift.

## What actually predicts the price

| Predictor | Pearson | t (n=92) | |
|---|---:|---:|---|
| **Population** | **-0.355** | **3.60** | significant |
| Median income | -0.233 | 2.28 | significant |
| % Black | +0.215 | 2.09 | significant, raw |
| Class I differential | +0.212 | 2.06 | significant |
| % Hispanic | -0.136 | 1.31 | no |

Market size is the strongest single predictor, and it is monotonic:

| Population quartile | n | Median $/gal | Mean % Black |
|---|---:|---:|---:|
| 9.8k–19.5k | 23 | **$3.82** | 29.9% |
| 19.5k–29.8k | 23 | $2.97 | 29.4% |
| 30.1k–41.2k | 23 | **$2.70** | 26.1% |
| 41.6k–67.7k | 23 | $2.86 | 19.1% |

The smallest markets pay **$1.12 more** than mid-sized ones for the same gallon.

## On the race question

The raw correlation between a ZIP's Black share and its Walmart milk price is **+0.215 (t=2.09)** — nominally significant, and unlike Aldi, where it was zero across 350 ZIPs. But it does not survive a single control:

| Controlling for | Partial r | t | |
|---|---:|---:|---|
| nothing (raw) | +0.215 | 2.09 | significant |
| population | +0.156 | 1.49 | not significant |
| **median income** | **+0.086** | **0.81** | not significant |
| Class I differential | +0.158 | 1.51 | not significant |

Stratifying makes the same point more bluntly: within rural stores the correlation is +0.219 (t=1.69, not significant), and **within urban stores it reverses to -0.168**. A relationship that changes sign between strata is not a pricing rule.

The reason is entanglement: in this sample %Black correlates **-0.648** with median income. Race and income are close to the same variable in rural South Carolina, and with 92 stores they cannot be separated.

**The defensible statement:** Walmart's SC milk price tracks market size and income, both of which correlate with racial composition in this state. There is no evidence of pricing *on* race, and there is clear evidence of a rural premium that falls disproportionately on ZIPs that are poorer and more Black.

## The Class I differential is not the explanation

The federal Class I differential — the actual regulated cost input — ranges only **5.6 to 6.0 $/cwt** across these stores, about 3 cents a gallon. It correlates +0.212 with price, but it cannot produce a $1.50 spread. Walmart's rural premium is a pricing decision, not a milk-cost pass-through.

## Caveat on the Aldi side

Aldi's ZIP prices come from its delivery storefront, which returns a serving zone's price for any SC ZIP — including ZIPs with no nearby Aldi. Aldi has a limited SC footprint, so in the rural ZIPs where Walmart's premium is largest, **Aldi may not be a store a shopper can actually reach.** The gap is real as a price comparison; it is not proof that a cheaper gallon is locally available.
