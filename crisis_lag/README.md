# crisis_lag

The falsification test for *The Preconditions: Money, and the Wars Europe Could
Not Afford, 1905–1914*.

> **The central testable claim.** In each pre-war crisis the lag from *crisis
> onset* to *peak financial stress* — read off the sovereign spread series — was
> consistently **~6–10 weeks**. The July 1914 decision window was **~5 days**. If
> so, the financial brake did not fail in 1914; it was given a fifth of the time
> it needed. This package measures those lags and adjudicates the claim.

**"Brake" means the *market's* capacity to react in time — mechanism, not motive.**
No one is claimed to have timed the crisis to defeat the money market; the July
tempo's documented motives are diplomatic. The financial *effect* (a market that
could not price what it could not see) does not require financial *intent*. See
[`../docs/july1914_mechanism_and_archival_test.md`](../docs/july1914_mechanism_and_archival_test.md).

## Status: run on real data — and it does **not** support the 6–10 week clock

The instrument has now been run on real sovereign spreads, built from the
mirrored Neal-Weidenmier weekly bonds (`build_nw_spreads.py` →
`data/nw_spreads_long.csv`). The measured result (full write-up:
[`results/measured_lags_nw.md`](results/measured_lags_nw.md)):

| crisis | onset→peak lag | onset→material |
|---|---|---|
| Morocco 1905 (russia) | 16.0 wk | 15.0 wk |
| Bosnia 1908 (russia) | 16.4 wk | 1.4 wk |
| Agadir 1911 (germany) | 16.9 wk | — |
| Balkans 1912–13 (austria) | 37.4 wk | 1.4 wk |
| **July 1914** | censored | window **0.7 wk** |

**Peak-stress lags are 16–37 weeks — 2–4× the asserted 6–10, none in the band**
(verdict INCONCLUSIVE; robust to using raw yields instead of spreads). So the
specific "6–10 weeks" figure is not what the data show. The *directional*
argument survives — July 1914's 0.7-week window is dwarfed by any of these lags —
but the honest mechanism is "peak stress took **months**, and 1914 truncated it
at t0," with the fast *material* onsets (Bosnia, Balkans ~1.4 wk) acknowledged.
Caveats (provisional onsets; Morocco→russia confounded by the 1905 revolution) in
the write-up. The earlier synthetic tests remain, as instrument checks.

## What it does

```
tidy series ──▶ per-crisis baseline (pre-onset) ──▶ abnormal stress (z)
                                                         │
        VERDICT ◀── adjudicate ◀── onset→peak-stress lag ┘   + July 1914 window
```

- **Source-agnostic input.** Consumes the tidy long `(date, series, value)` CSV
  emitted by `gallica_le_temps.series`, so **monthly IMM spreads** (cross-crisis
  regularity) and **daily Le Temps quotations** (1914 sharpening) feed the same
  instrument. `value` is the stress measure — a spread in bp, a yield, a price.
- **Baseline before onset.** Each crisis gets a pre-onset baseline window; stress
  is the spread *above* that baseline (level and z-score), so a raw maximum can't
  masquerade as crisis stress and the search can't leak into the normalisation.
- **Two lags.** *time-to-peak* (max spread in the search window) and
  *time-to-material* (first crossing of `z_threshold` above baseline). Both in weeks.
- **July 1914 is censored, not measured.** The bourses closed, so its peak is
  right-censored; it carries a decision-window length (~5 days) that the verdict
  contrasts against the comparators' lags.

## Usage

```bash
cd crisis_lag && pip install -e .
crisis-lag run spreads_long.csv                    # built-in crises + verdict
crisis-lag run spreads_long.csv --events e.yaml     # your event spec
crisis-lag run spreads_long.csv --measure material --band 6 10 --floor 2
```

Exit code is non-zero when the verdict is `FALSIFIED`, so it can gate a build.

## The verdict logic (pre-registered)

Fix these **before** looking at 1914:

- **band** = predicted lag band, default **6–10 weeks**.
- **floor** = falsification floor, default **2 weeks**.
- `CORROBORATED` — comparator lags all clear the floor, sit (all but at most one)
  in the band, and exceed the 1914 window by a clear margin.
- `FALSIFIED` — **any** comparator peaked in under the floor: a crisis that became
  material in days means the brake could have bitten inside July 1914's window,
  and the "needs weeks" mechanism fails.
- `INCONCLUSIVE` — above the floor but not tight in the band, or no comparators.
  With a handful of crises and monthly data, this is an honest outcome, not a fudge.

## Event specification — PROVISIONAL, needs reconciliation

`events.py` ships default onset dates and a binding-power→series mapping for the
five crises. **These are provisional.** The onset dates and *which power's spread
carries each crisis* are exactly the "event dates and specification" to reconcile
against the original thesis dataset. Override everything via YAML:

```yaml
events:
  - name: Agadir_1911
    onset: "1911-07-01"     # Panther at Agadir
    series: germany          # the fiscally-binding power that crisis
    search_days: 180
  - name: July_1914
    onset: "1914-07-23"     # Austrian ultimatum
    series: austria_hungary
    measurable: false        # bourses closed -> peak censored
    decision_window_days: 5
```

Defaults (all overridable): Morocco 1905-03-31 (France/Russia), Bosnia 1908-10-06
(Russia), Agadir 1911-07-01 (Germany), Balkans 1912-10-08 (Austria-Hungary),
July 1914 1914-07-23 (Austria, censored).

## Seasonal (control-year) baseline — `--seasonal`

Money-market rates tighten every autumn. Since a summer onset is baselined on the
calm spring and its peak is searched into the autumn, that seasonal tightening can
masquerade as crisis stress (the raw Berlin rate "spiked" into September 1911, but
rose *more* in the calm year 1910 — pure seasonality). `--seasonal` removes it:

```bash
crisis-lag run weekly_long.csv --events events.yaml --seasonal            # by month
crisis-lag run weekly_long.csv --events events.yaml --seasonal-unit week  # finer
```

It estimates a normal value for each calendar unit from the years with **no coded
crisis**, subtracts it, then runs the usual baseline/peak machinery on the
residual. Because the pre-onset baseline is then computed on the residual, the
crisis year's own level offset is differenced out too — a difference-in-differences
(`crisis_lag.seasonal`). It is a strict generalisation: flat seasonality ⇒ the
plain method.

**What it shows, and a caveat that matters.** On the real legs the **peak** lag is
robust to it (Agadir ~20 wk, Balkans ~26 wk — verdict stays INCONCLUSIVE, nothing
falsified). But deseasonalising **shrinks the baseline variance**, so the z-based
**`material`** measure gets more sensitive: with the objective (mid-crisis) Balkans
onset, Austria's spread reads "material" within ~0.3 wk — which flips a
`--measure material` run to FALSIFIED. That is *not* a clean refutation: the
objective onset (1912-11-21) sits mid-crisis, so stress had already built before
it, and a tiny post-deseasonalisation baseline sd inflates z. Read the **peak**
measure as the robust headline; treat seasonal + `material` together as a
sensitivity probe, not a verdict.

## Known limits (state them, don't paper over them)

- **n is small.** Four comparators is a range check, not a powered test. Widen it
  (Fashoda 1898, Liman von Sanders 1913, the two Balkan Wars separately) to give
  the band any power.
- **The `material` measure is variance-sensitive**, especially with `--seasonal`
  (which shrinks the baseline sd): a small, stable pre-onset window can make an
  ordinary move cross the z threshold early. Prefer `peak` for the headline.
- **Monthly resolution can't see a 5-day window.** The IMM is monthly; it
  establishes the cross-crisis regularity but cannot characterise 1914 — that is
  what the weekly *Chronicle* and daily *Le Temps* sources are for.
- **Coupon dates.** Sovereigns go ex-coupon on fixed dates; a mechanical drop can
  masquerade as stress. Feed clean/flat quotations.

## Tests

```bash
python -m pytest -q      # 27 tests, no network
```
