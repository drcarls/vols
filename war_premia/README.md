# war_premia

Reproduce and extend **Carls (2005)**, *"Did Politicians Cry 'War' to Financial
Markets Once Too Often? An Examination of War Risk Premia Prior to World War I."*

Rigobon-Sack **identification-by-heteroskedasticity** of war-risk premia in the
weekly city money-market rates of the **Neal-Weidenmeier Gold Standard Database**
(mirrored in [`../neal_weidenmier`](../neal_weidenmier)). For each city rate `x`
and the London 3-month trade bill basis `y`, it regresses Δx on Δy with an
instrument built from the war/non-war regime sign, `w = ±Δy`, so the war-risk
factor is identified without being quantified.

```bash
cd war_premia && pip install -e .
war-premia reproduce     # Tables 3-7 on the mirrored NW short rates
war-premia july1914      # the extension + why the July-1914 premium isn't estimable
```

## Reproduction

`results/reproduction_tables.txt` is the committed output. The full sub-sample
(the paper's Table 7, the best-powered) matches closely:

| city (open-market) | paper | this repo |
|---|---|---|
| Paris | 0.11 (t 3.20) | **0.11 (t 3.46)** |
| Amsterdam | 0.09 | **0.09** |
| Copenhagen | 0.14 | **0.14** |
| Berlin | 0.38 (t 6.58) | 0.35 (t 6.40) |
| Vienna | 0.17 | 0.13 |
| Brussels | 0.21 | 0.18 |
| Geneva | 0.07 | 0.09 |
| New York | −0.23 | **−0.33** (safe haven) |

First Moroccan reproduces too (Geneva 0.30 = 0.30, Copenhagen 0.14 = 0.14, Paris
0.51 vs 0.46). The small-n crises (Second Moroccan n=22, Balkans) are noisy and
sensitive to the exact war-week→week mapping and window endpoints — the
imprecision the paper itself flags. Differences trace to (a) the First Moroccan
window is inferred (the paper gives n=62, not endpoints) and (b) event→Saturday
mapping conventions.

## The July-1914 extension — and why it can't be a Rigobon-Sack premium

The estimator needs a **war-week variance regime**. July 1914 denies it one on
*both* assets, because the markets closed exactly when war came:

- **Short-term rates end 1914-06-27**, the eve of Sarajevo (28 June). Every
  July-1914 war event is after the data — one boundary week, no crisis response.
- **Long-term bonds are monthly with a 63-day gap, 1914-06-03 → 1914-08-05**,
  straight across the crisis. One observation spans it — no regime to identify.

This is not a coding gap; it is the central empirical fact. The event that would
have revealed whether markets had finally stopped "crying wolf" is the one where
the markets stopped trading.

### The bond cross-section is uninterpretable (a withdrawn result)

An earlier version reported a June-3 → Aug-5 bond "cross-section" (Consols −0.3%,
French −1.8%, …) and read it as a trivially small, Ferguson-flat move. **That is
withdrawn.** Auditing the raw column (`war-premia july1914`, `bond_quote_audit`):

- The quotes are **prices** (points of par), not yields.
- The **June-3 baseline is ex-dividend** — Consols 76.75 (Jun 2) → 75.0 `xd`
  (Jun 3), a mechanical coupon drop, not a market move (same for the Russian 1822).
- The **post-closure quotes are not genuine trades**: Russian and Austrian bonds
  *rise* Aug→Sep 1914 (Austrian Gold 84→89, Russian 1822 120→125) — impossible for
  belligerent debt at war. They are nominal quotes carried through the closure.

Comparing a stale August quote to an ex-dividend June baseline manufactured the
spurious ~2%. The cross-section can't be interpreted at all.

**The one genuine signal** (from the workbook's own NOTES sheet): the London price
of the **French 3% rente fell 80 → 76.5 on 30 July 1914 — ~−4.4% in the final
trading week**, and accelerating. With the money market seizing the same week
(Bank of England 3 → 4 → 8 → 10%), that is a market **routing as it shut**, not a
flat one. The full war shock is unobservable: trading stopped mid-repricing.

### The money market through July–August 1914 (descriptive)

The NW short rates end 1914-06-27; `data/july_aug_1914_money.csv` fills the war
weeks from the **Commercial and Financial Chronicle** (public domain, via FRASER /
Wayback), each figure carrying its OCR source quote. It is descriptive, not
identified. Two findings (see `results/july_aug_1914_money.md`):

- **No anticipation.** London 3-month bills drift ~1.9%→2.4% through July — an
  ordinary summer firming, no war being priced — then the market froze (LSE closed
  31 July). Ferguson again, in the short rates.
- **A convulsion, then the data goes dark.** When war came the Bank of England
  rate went **3 → 4 → 8 → 10%** in a week and NY call money to 7%. The bond market
  was routing too — the London French rente fell ~4.4% in the final trading week —
  but then trading stopped, and its post-closure quotes are nominal, not real
  (see the audit above). The *war premium* is unobservable: the market shut
  mid-repricing.

### NYC bonds, 1914: the closure and the reopening

`data/nyc_1914_bonds.csv` + `results/nyc_1914_bonds.md` (sourced to the *Chronicle*,
via FRASER/Wayback) cover the New York case, which ran on a **different mechanism**.
The US was a *debtor*: at the outbreak Europe dumped American securities for gold
($41.85M engaged in the first week), so the NYSE closed 31 July to stop the selling
and the gold drain — the US defending its gold, not a belligerent its debt. The
Aug–Nov closure quotes are minimum-price floors (excluded). The genuine, observable
reaction is the **28 Nov 1914 bond reopening**, and it was **firm**: trading resumed
"without a hitch," high grades near par — US Steel 5s 99¾–100¼ (the week's most
active), US Rubber 6s above par, short high grades ~99–100¼. NYC bonds did not
crash; the crash was pre-empted by closure, and US credit was, if anything, a war
beneficiary.

## St. Petersburg (Russia) — a series the original couldn't include

The paper reported the Russian market rate as unavailable. The NW short-rate file
carries a **St. Petersburg *bank* rate** (the Russian State Bank discount rate),
populated weekly across 1904–1914 — so Russia can enter the estimation for the
first time. `war-premia russia` reports it.

The finding is itself informative: the St. Petersburg bank-rate premium is ≈ 0,
against Berlin 0.21 and Paris 0.05 (full-sample, *bank* rates). Russia's rate was
**administered and sticky** — the State Bank held it through crises where the
Reichsbank moved — so it carries almost no war-risk signal. That is a real
limitation of the Russian series, not evidence that Russia bore no war risk; only
its market (open-market) rate would show it, and that is the series NW lacks after
1900.

## Tests

```bash
python -m pytest -q      # estimator arithmetic + war-week coding, no network
```
