# Rigobon-Sack under a neutral basis — and a placebo that bites

> **Instrument: commercial paper, throughout.** Every premium here is on the
> short-term **money-market** rates — city *open-market* discount rates (Berlin,
> Paris, Vienna, Amsterdam), the Scandinavian and Swiss *market* rates, NY *call*
> money, and the London *3-month trade bill* as the basis. Not bonds. (This is what
> Carls's paper estimated, and the right instrument for the brake.) The Scandinavian
> Monetary Union bloc below could *only* appear in commercial paper — NW's bond file
> carries no Scandinavian series, and a currency union is a money-market phenomenon.

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

## The t-stats settle it: the premium is pooled-only and neutral-shared

Add significance to the time series and the "war-risk" reading largely dissolves.

**Berlin over time** (β, t vs London): First Moroccan +0.25 (t 0.97), Bosnia +0.02
(t 0.12), Agadir +2.17 (t 0.63), Balkans +0.26 (t 0.92), **Full +0.35 (t 6.40)**.
**Berlin is not significant in any single crisis** — every per-crisis t < 1. The
German premium exists *only* in the pooled sample.

**Neutrals, full-sample t:** Copenhagen +0.14 (**t 5.6**), Stockholm +0.12 (**t
4.3**), Christiana +0.08 (**t 3.3**), Geneva +0.09 (**t 2.8**), Amsterdam +0.09
(**t 2.2**) — all significant. The neutrals carry pooled premia as *significant* as
Berlin's (Copenhagen's t 5.6 rivals Berlin's 6.4). And per crisis: **in the Balkans
neutral Stockholm is significant (+0.34, t 3.4) while belligerent Berlin is not (t
0.92)**; in the First Moroccan crisis neutral Geneva is significant (+0.30, t 2.2).

So the coefficient is not cleanly a war-risk premium. It is a **loading on a common
London-centred money-market factor** — gold-standard integration that tightens
under stress — that *every* connected market carries, neutrals included, and that
is only statistically detectable by pooling. Berlin's loading is the **largest**
(0.35 vs the neutrals' 0.09–0.14), which is a real and interesting fact, but it is
a difference of degree on a shared factor, not a qualitatively distinct war
premium, and it cannot be seen crisis-by-crisis.

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

## How robust are the neutral premia? A Scandinavian bloc, not independent checks

Belligerents against *each* neutral basis, and the neutrals against each other
(`war-premia neutrals`, full sample). **Christiania = Oslo** (Norway's capital was
named Christiania until 1925).

**Belligerents' premium by neutral basis:**

| country | Amsterdam | Geneva | Stockholm | Copenhagen | Christiania | NewYork |
|---|---|---|---|---|---|---|
| **Berlin** | +0.07 | **+0.34** | **+0.26** | **+0.30** | +0.16 | −0.01 |
| Vienna | −0.04 | +0.08 | +0.21 | +0.12 | +0.05 | −0.00 |
| Paris | +0.04 | +0.10 | +0.13 | +0.18 | +0.13 | −0.00 |
| Brussels | +0.15 | +0.19 | +0.17 | +0.35 | +0.02 | −0.01 |

Berlin clears ~0.26–0.34 against **3 of 5** credible neutrals (Geneva, Copenhagen,
Stockholm); it is suppressed only against **Amsterdam** (the most Germany-integrated
neutral) and noisy NY. Vienna/Paris/Brussels stay at the floor whichever neutral
you pick.

**Neutral (x) vs neutral (basis):**

| x / basis | Amsterdam | Geneva | Stockholm | Copenhagen | Christiania |
|---|---|---|---|---|---|
| Amsterdam | — | 0.14 | 0.11 | 0.13 | 0.07 |
| Geneva | 0.09 | — | 0.15 | 0.19 | 0.16 |
| Stockholm | 0.05 | 0.11 | — | **0.54** | **0.61** |
| Copenhagen | 0.05 | 0.13 | **0.47** | — | **0.40** |
| Christiania | 0.02 | 0.09 | **0.43** | **0.33** | — |

The **Scandinavian trio — Stockholm, Copenhagen, Christiania — co-moves enormously**
(betas 0.33–0.61), because they *were* one market: the **Scandinavian Monetary
Union** (Denmark, Norway, Sweden on a shared gold krone, 1873–1914). So Copenhagen,
Stockholm and Christiania are **not three independent neutral checks — they are one
bloc**; Amsterdam and Geneva are more independent (betas 0.07–0.19). This sharpens
the robustness verdict: the neutral premia are a **common/bloc factor** (a
Scandinavian bloc plus a looser Amsterdam/Geneva), not independent country-specific
war risk — and the several significant "neutral premia" against London are closer
to ~three independent observations than six. Berlin's premium is the more robust of
the two sides (surviving 3 of 5 neutral bases), but it too leans on treating
Amsterdam as compromised.

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
