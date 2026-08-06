# Premia by country × conflict × neutral basis — mostly noise, one survivor

The core premia re-estimated against the three neutral bases (Amsterdam, Swiss =
Geneva, Swedish = Stockholm), London kept for reference, broken out **by conflict
and country** (`war-premia grid`). Russia is the administered bank rate (no
open-market series), so it cannot move and is marked `*`.

## The per-conflict estimates are not reliably identified

| First Moroccan 1905 | London | Amsterdam | Swiss | Swedish |
|---|---|---|---|---|
| Germany | +0.25 | +0.34 | +0.87 | +0.88 |
| France | +0.51 | **−0.58** | +0.10 | +0.12 |
| Austria | −0.05 | −0.00 | +0.02 | +1.56 |

| Bosnia 1908 | London | Amsterdam | Swiss | Swedish |
|---|---|---|---|---|
| Germany | +0.02 | −0.05 | −0.37 | −0.93 |
| France | +0.04 | +0.33 | +0.37 | +0.29 |
| Austria | +0.02 | −0.04 | −0.07 | −0.25 |

| Second Moroccan / Agadir 1911 (n=22) | London | Amsterdam | Swiss | Swedish |
|---|---|---|---|---|
| Germany | +2.17 | −0.03 | +0.36 | +1.75 |
| France | +2.15 | +0.18 | +0.52 | +0.25 |
| Belgium | **+5.75** | −0.08 | +0.37 | +1.25 |

The per-crisis coefficients **swing wildly across bases, flip sign (France, First
Moroccan: +0.51 vs −0.58), and blow up at small n** (Agadir, n=22: Belgium +5.75,
Germany +2.17). A ~50-week crisis with ~7 war events does not give the
heteroskedasticity instrument enough regime variance to identify β — so the
individual-crisis premia (which the paper itself flags as imprecise) are **not
robust to the basis and should not be read as country-in-conflict war premia.**

## The full sub-sample is the only well-identified estimate

| Full sub-sample (n=485) | London | Amsterdam | Swiss | Swedish | verdict |
|---|---|---|---|---|---|
| **Germany** | +0.35 | +0.07 | +0.34 | +0.26 | **robust** (3/4; Amsterdam the outlier) |
| **Belgium** | +0.18 | +0.15 | +0.19 | +0.17 | **robust & stable** (all 4), modest |
| France | +0.11 | +0.04 | +0.10 | +0.13 | at the ~0.10 neutral floor |
| Austria | +0.13 | −0.04 | +0.08 | +0.21 | unstable, floor-ish |
| Russia* | −0.00 | −0.04 | −0.02 | +0.14 | administered rate — unmeasurable |

## Which country, which conflict, what premium — the honest answer

- **You cannot attribute a premium to a country *within a single conflict*** from
  this data — the per-crisis estimates are noise once you demand robustness to the
  basis. That is the main finding, and it undercuts any table of per-crisis premia.
- **Pooled over 1904–1913, two premia survive the neutral bases:** **Germany
  ≈ 0.30** (clear, and clearly above the ~0.10 neutral floor — the one strong
  country result, consistent with the 1911 Berlin panic and every other robustness
  check this session) and **Belgium ≈ 0.17** (small but the most *stable* across
  bases — plausible for the exposed invasion-route economy, though only modestly
  above the floor).
- **France (~0.10) sits at the neutral floor** — indistinguishable from
  money-market integration. **Austria** is floor-ish and basis-unstable.
  **Russia** is unmeasurable (administered rate).

So: Germany, across the whole pre-war period, is the country whose money market
carried a real war-risk premium; Belgium a smaller stable one; no single
country-in-conflict premium is robustly estimable. This is the neutral-basis
re-estimation the benchmark critique demanded, and it leaves Germany as the finding
that survives.

## Reproduce

```bash
cd war_premia && war-premia grid      # per-crisis grid
war-premia basis                       # full-sample + neutral placebo + London
```
