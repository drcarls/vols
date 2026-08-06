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

### What is observable — and its two readings

The single bond change spanning the closure (a raw event change, **not** a
heteroskedasticity premium, and a **distorted lower bound** — the closure and
support operations froze quoted prices):

| sovereign | 1914-06-03 → 1914-08-05 |
|---|---|
| UK Consols 3% | −0.3% |
| Austrian Gold 4% | −1.2% |
| French 3% rentes | −1.8% |
| German Imperial 3% | −1.9% |
| Russian 4% / 5% | −2.2% / −2.4% |

**Both readings must be stated, and the second is the headline:**

- **Ordering (the smaller point, mine):** belligerents fell most, British Consols
  least — the paper's belligerent-vs-haven cross-section, at the moment war came.
- **Magnitude (the larger point, Ferguson's):** a ~2% fall on the *outbreak of a
  world war* is almost nothing. The bond market **did not price the war**, even as
  it began — markets were caught off guard. The ordering rides on top of a shock
  that is, in absolute terms, trivial. This confirms Ferguson; it does not refute
  him.

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
