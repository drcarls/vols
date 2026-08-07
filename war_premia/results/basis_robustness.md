# Rigobon-Sack under a neutral basis — and a placebo that bites

The premia are estimated against the **London 3-mo trade bill** as the basis
asset. But London is a great-power money market that itself moves with war (see
`../../crisis_lag/results/uk_benchmark_check.md`). So re-estimate against neutral
bases, and placebo-test the neutrals themselves (`war-premia basis`).

## Premium (single-IV β, full sample) by basis asset

| basis | Berlin | Paris | Vienna | St Petersburg |
|---|---|---|---|---|
| **London trade (orig)** | **0.35** | 0.11 | 0.13 | −0.00 |
| **Switzerland (Geneva)** | **0.34** | 0.10 | 0.08 | −0.02 |
| Sweden (Stockholm) | 0.26 | 0.13 | 0.21 | 0.14 |
| Amsterdam (near neutral) | 0.07 | 0.04 | −0.04 | −0.04 |
| US call money | −0.01 | −0.00 | −0.00 | 0.01 |

- **Berlin is robust** — 0.34–0.35 against both the London and the Swiss basis, and
  roughly holds under Sweden (0.26). It **collapses only** under the Amsterdam and
  US bases, which are bad bases (Amsterdam is itself war-sensitive, so subtracting
  it removes the common factor; US call money is too volatile — 1907 panic, no
  pre-1913 central bank — to identify anything).
- **Paris and Vienna do not survive as cleanly** — small and basis-sensitive.

## Where the neutral premia come from — and how they look over time

The neutral premia are estimated exactly like any city's: the neutral as the
regressand `x` against the London basis, β read off (`war-premia matrix`). They are
**full-sample pooled** numbers, and over time they are as noisy as everyone's:

**Premium vs London basis, city × crisis (~ = neutral):**

| city | First Mor. | Bosnia | Agadir (n=22) | Balkans | **Full** |
|---|---|---|---|---|---|
| Berlin | +0.25 | +0.02 | +2.17 | +0.26 | **+0.35** |
| Paris | +0.51 | +0.04 | +2.15 | −0.07 | +0.11 |
| Vienna | −0.05 | +0.02 | +1.41 | +0.13 | +0.13 |
| **Stockholm~** | −0.00 | **−0.21** | +1.33 | **+0.34** | **+0.12** |
| Amsterdam~ | −0.08 | −0.04 | +0.35 | +0.04 | +0.09 |
| Geneva~ | +0.30 | +0.01 | +1.25 | +0.05 | +0.09 |
| Copenhagen~ | +0.14 | −0.03 | +1.67 | −0.00 | +0.14 |
| NewYork~ | +0.14 | −0.36 | +0.76 | −0.44 | −0.33 |

**Stockholm's premium over time:** −0.00 → −0.21 (Bosnia) → +1.33 (Agadir, t=0.7,
junk) → +0.34 (Balkans, t=3.4) → **+0.12 full (t=4.3)**. So the "0.12 neutral floor"
is a **pooled** number, not a stable per-crisis level — it is near zero or negative
in most crises and the pooled positive comes mostly from the **Balkans**. Two
consequences: (i) the neutral floor is a pooled artifact driven by specific periods
of money-market integration, not a constant; (ii) **in the Balkans, neutral
Stockholm (+0.34) outscores belligerent Berlin (+0.26)** — a neutral beating a
belligerent, the sharpest sign that the premium is not cleanly war risk. Only
Berlin's full-sample ~0.35 stands clearly *and* consistently (positive in every
identified crisis) above the neutral cluster.

## The placebo: genuine neutrals carry "war premia" too

Premium *of* each neutral, basis = London (a true neutral should be ~0):

| neutral | β | t |
|---|---|---|
| Amsterdam | +0.09 | 2.2 |
| Switzerland (Geneva) | +0.09 | 2.8 |
| Sweden (Stockholm) | +0.12 | 4.3 |
| US call money | −0.33 | −1.1 (noise) |

**The neutrals show premia of 0.09–0.12 — the same size as Paris (0.11) and Vienna
(0.13).** This is already latent in the paper's own table (Amsterdam 0.09, Geneva
0.07, Copenhagen 0.14 sit right among the belligerents). So the Rigobon-Sack
premium is not cleanly a *war-risk* measure: against a war-sensitive money-market
basis it picks up a common **war-week money-market integration** that every
European market shares (~0.10), whether belligerent or neutral. Whether that 0.10
is genuine partial exposure (Amsterdam borders Germany; Switzerland is landlocked
among powers; Sweden sits on the Baltic) or a pure method artifact, the practical
consequence is the same.

## London itself is not a neutral basis — it is belligerent-grade

Swap the roles: measure **London** as the city against neutral bases.

| London rate | vs Amsterdam | vs Switzerland | vs Sweden |
|---|---|---|---|
| BoE rate | +0.17 | +0.23 | +0.38 |
| 3-mo trade bill | +0.13 | +0.22 | +0.38 |
| 90-day bank bills | +0.09 | +0.28 | +0.42 |

Against Switzerland and Sweden, **London's premium (0.22–0.42) matches Berlin's**
(0.26–0.34 against the same neutrals). So London is one of the **two most
war-sensitive** money markets, not a war-neutral reference — historically exact, as
London was the global bill/acceptance/gold centre and froze hardest in July 1914
(BoE to 10%, the acceptance market seized, the Exchange closed). This is the
strongest form of the benchmark critique: **the paper's basis asset is itself
belligerent-grade war-sensitive**, so every city premium measured against it is
differenced against a war-moving reference — which compresses the premia and
distorts their ranking. The asymmetry seals it: neutrals show only ~0.10 against
London, but London shows 0.22–0.42 against neutrals.

## What survives

- **Berlin's premium is the one that clearly clears the ~0.10 neutral floor** and
  is basis-robust (London *and* Swiss). Germany genuinely carried a larger
  money-market war premium — consistent with the 1911 Berlin panic and with
  Germany being the more robust case in the cause-or-cover far-neutral test.
- **Paris and Vienna sit *at* the neutral floor**, so their premia cannot be
  cleanly separated from money-market integration. The paper's cross-city ranking
  interleaves belligerents and neutrals (Berlin » Brussels 0.21 > Vienna 0.13–0.17
  ≈ Copenhagen 0.14 ≈ Paris 0.11 ≈ Amsterdam 0.09 ≈ Geneva 0.07) — only the top
  (Berlin) stands apart.
- **St Petersburg is ~0 across bases**, but that is the *administered bank rate*
  (sticky by construction — see the Kokovtsov analysis), a data gap, not evidence
  that Russia bore no war risk.

## For the book

- **Report premia relative to the ~0.10 neutral placebo floor, not against zero.**
  Against that floor only Berlin clearly separates; present Paris/Vienna/the
  neutrals as a cluster that the method cannot cleanly rank by war risk.
- **The London basis reproduces on a Swiss basis** for Berlin — so the headline
  German result is not an artifact of the contaminated London basis. Say so; it is
  a real robustness win for the one premium that matters most.
- **Add the neutral placebo to the paper** as the honest yardstick: it is the
  cleanest way to show which premia are war risk (Berlin) and which are plausibly
  integration (the rest).

## Reproduce

```bash
cd war_premia && war-premia basis
```
