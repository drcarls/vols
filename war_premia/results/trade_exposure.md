# Testing the blockade / trade-exposure channel — and it holds (modestly)

Does the neutral war-risk premium scale with **trade dependence on the Central
Powers** — the trade the British blockade actually severed? Earlier I said this
couldn't be tested (n≈3, no data). That was premature: expanding the cross-section
to **Italy, Spain and Portugal** (open-market rates NW also carries) gives eight
European neutrals, and the **Correlates of War Bilateral Trade v4.0** dataset
supplies real 1913 trade shares. Run it (`trade_exposure.py`):

## Data

- **y** = full-sample Rigobon-Sack money-market premium (vs the London basis), from
  the Neal-Weidenmier short rates.
- **x** = 1913 trade with Germany / with the Central Powers (Germany+Austria) / with
  all belligerents (DE, AT, UK, FR, RU), as a share of each country's total trade —
  extracted from the COW dyadic file (`data/cow_trade_shares_1913.csv`).

| country | premium β | %Germany | %Central | %Bellig |
|---|---|---|---|---|
| Denmark | 0.14 | 32.1 | 33.1 | 75.8 |
| Sweden | 0.12 | 29.2 | 29.2 | 67.1 |
| Italy | 0.12 | 16.1 | 23.9 | 49.4 |
| Netherlands | 0.09 | 19.1 | 19.1 | 32.7 |
| Switzerland | 0.09 | 27.6 | 33.4 | 63.2 |
| Spain | 0.09 | 18.6 | 19.4 | 65.6 |
| Norway | 0.08 | 26.2 | 26.2 | 61.8 |
| Portugal | 0.01 | 14.9 | 16.4 | 48.8 |
| *USA* | *−0.33* | *13.8* | *14.8* | *44.9* |

## Result — the right sign, moderate, marginally significant

**Within the eight European neutrals:**

| x | Pearson r | Spearman | t (df 6) |
|---|---|---|---|
| **% trade with Central Powers** | **+0.64** | +0.48 | **2.02** |
| % trade with Germany | +0.53 | +0.52 | 1.55 |
| % trade with all belligerents | +0.38 | +0.43 | 1.00 |

Neutrals more dependent on **Central-Powers** trade carried **higher** war premia —
the direction the blockade channel predicts, at a moderate-to-strong r ≈ 0.6.
Denmark (32% Central, β 0.14) and Sweden (29%, 0.12) anchor the high end; Portugal
(16%, β 0.01) the low. Central-Powers share beats all-belligerent share, exactly as
"the trade the blockade cut" should.

**But it is suggestive, not conclusive.** n = 8, and three of the eight are the
Scandinavian monetary-union bloc (so effective n is smaller); t = 2.0 on the best
variable is borderline. Adding the belligerents washes it out (their premia are
idiosyncratic, driven by *being* belligerents — r falls to 0.26), as it should.

## The US is the informative break

The US has **high belligerent trade (44.9%)** yet a **negative** premium. High trade
*volume* with the belligerents did not raise its premium, because the US was a war
**supplier and creditor — a beneficiary, not a disrupted neutral** (gold flowed in;
it is the R²≈0 outlier on the common factor). So the channel is not trade volume per
se but **disruptive dependence**: being cut off from, or fought over, versus selling
into the war. Central-Powers dependence captures the first; the US embodies the
second. That refines your hypothesis rather than contradicting it.

## Robustness — and it is *not* robust to the premium measure

Is the r = 0.64 an artifact of measuring the premium against the London basis?
Recomputing the same correlation with other premium measures:

| premium measure | r (premium vs %Central) |
|---|---|
| London-basis β | **+0.64** |
| common-factor loading | +0.41 |
| **Swiss-basis β** | **−0.01** |

Positive on the London basis and the common-factor loading, but it **vanishes on the
Swiss basis.** There is a mechanical reason — Geneva (Switzerland) is itself the
*highest* Central-Powers-trade neutral (33.4%), so using it as the basis differences
the shared trade-exposure component away, which is a contaminated basis for *this*
test. But that excuse cannot fully rescue it: the result is measure-dependent.

## Verdict — suggestive, fragile, not confirmed

Honest bottom line: within the eight neutrals the premium **does** rise with
Central-Powers trade dependence — the blockade channel's predicted sign, r ≈ 0.64 on
the London-basis premium (r ≈ 0.41 on the common factor) — but it is **underpowered**
(n = 8, three of them the Scandinavian bloc), only marginally significant, and **not
robust** to the premium measure (≈ 0 on the Swiss basis). So it is a *suggestive*
result, not a confirmed one — the same fragility every finding in this reanalysis has
shown once pushed. The US remains the clean qualitative point: high belligerent trade
but a negative premium, so exposure is disruptive *dependence*, not volume. A real
confirmation needs the direct instrument (marine war-risk insurance / freight rates)
and a cross-section large enough that no single basis choice or Scandinavian bloc can
swing it.

## Why no further test can harden this (where to stop)

The two natural next instruments both fail for structural reasons, so this
money-market cross-section is the best obtainable test — stop here:

- **Bonds.** NW's long-bond file has only *two* European neutrals (Netherlands,
  Italy); n≈2 can't test the hypothesis.
- **Marine war-risk insurance / freight rates.** (i) *Global*, not country-specific
  — a single series cannot run the cross-sectional exposure test; (ii)
  *peacetime-uninformative* — war-risk cover only priced once war was imminent, so
  the signal is the August-1914 spike (censored / descriptive), not the pre-war
  crises, which resolved short of war and moved freight via the business cycle.
  (Klovland's monthly indices exist but only inside paper appendices.)

So: the direction is right and consistent (and the US break confirms it is
disruptive *dependence*, not volume), but the magnitude is fragile and no obtainable
data escapes the small-n / basis-sensitivity ceiling. The honest book claim is the
*direction plus the US mechanism*, offered as suggestive evidence, not a coefficient.

## The marine-insurance channel: where the real data lives (access map)

The direct instrument (marine war-risk rates) would corroborate the mechanism but is
**archival, not a dataset** — and it is a global/route series, so it cannot run the
country cross-section anyway. Where it actually lives (checked; none is a download):

- **Lloyd's List** (London, daily) — digitized on the *British Newspaper Archive*
  (~271k pages) but **paywalled**; OCR of a daily paper.
- **The Economist** — *Economist Historical Archive* (Gale), **paywalled**.
- **The Statist** (London, weekly) — scattered public-domain volumes on Google
  Books / HathiTrust; no clean run located.
- **Journal of Commerce & Commercial Bulletin** (New York) — not digitized as a
  continuous run.
- **Hansa: Deutsche Nautische Zeitschrift** (Hamburg) — HathiTrust Record
  000599288 (1891–1925), likely limited-view / Cloudflare-walled; German OCR.
- **Assicurazioni Generali** ledgers (Trieste) — **physical corporate archive**.

Building a continuous weekly series from these is a multi-month transcription
project (cf. the July–Aug 1914 *Chronicle* OCR here, which took real effort for ~6
weeks). **Do NOT synthesise it** — a skeleton of invented anchors + interpolation +
noise is fabrication, not reconstruction, and a regression on it merely returns the
spikes hard-coded into it. The tractable slice is targeted OCR of the *Economist* /
*Statist* for the crisis weeks (late July 1911; late July–Aug 1914) — real sourced
quotations for a footnote, not a 762-week dataset.

## Sources

- Trade: **Correlates of War Bilateral Trade v4.0** — Barbieri, Katherine, Omar M. G.
  Keshk, and Brian Pollins (2009), "Trading Data," *Conflict Management and Peace
  Science* 26(5): 471–491. Dyadic file, 1913; shares in `data/cow_trade_shares_1913.csv`.
- Premia: Neal-Weidenmier short rates via `war_premia`.

## Reproduce

```bash
cd war_premia && python trade_exposure.py
```
