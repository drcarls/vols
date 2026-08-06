# Measuring the transmission lag — the "6–10 weeks" claim, run on real data

The draft asserts, throughout, that pre-war crises took **6–10 weeks** to travel
from onset to peak financial stress — and that July 1914's ~5-day decision window
was therefore a fraction of what the financial brake needed. That lag had been
*asserted*, not *measured*. It is measurable on data already in this repo, so
this is the measurement.

**Method.** Sovereign spreads (country current-yield − British-consol yield, in
yield points) built from the Neal-Weidenmier weekly bond prices
(`build_nw_spreads.py` → `data/nw_spreads_long.csv`), fed to `crisis-lag` with
the default event/onset/binding-power mapping. Onset→peak and onset→"material"
(first z>2 above a pre-onset baseline) lags, in weeks.

```
crisis            series          onset       peak         lag(wk)  material(wk)
Morocco_1905      russia          1905-03-31  1905-07-21     16.0      15.0
Bosnia_1908       russia          1908-10-06  1909-01-29     16.4       1.4
Agadir_1911       germany         1911-07-01  1911-10-27     16.9        -
Balkans_1912_13   austria_hungary 1912-10-08  1913-06-27     37.4       1.4
July_1914         austria_hungary 1914-07-23  window 0.7 wk    -         -
VERDICT: INCONCLUSIVE — lags 16.0/16.4/16.9/37.4; 0/4 in the 6–10 wk band.
```

## The measured lag depends entirely on which lag you mean

The "6–10 weeks" is not robustly recovered — but the honest finding is that the
answer is **operationalization-dependent**, not simply "longer":

- **Onset→peak lag is 16–37 weeks** — 2–4× the asserted figure, 0 of 4 in the
  band, robust to spreads vs raw yields. On *this* measure the claim is not
  supported. But a peak searched over a 6–10 month window can be set by
  late-crisis or non-crisis drift (the Balkans peak is June 1913, mid-Second-
  Balkan-War), so it is arguably not the right operationalization of "the brake
  bit."
- **Onset→material lag (first z>2) is 1–15 weeks** — ~1.4 wk (Bosnia, Balkans),
  8–15 wk (Morocco, Agadir). This *brackets* the 6–10 week claim rather than
  refuting it: significant stress can arrive within days in some crises and take
  months in others.

So the number is not so much *wrong* as *underdetermined*: a single "6–10 weeks"
compresses a lag that is fast-to-material in some crises, slow-to-peak in all, and
sensitive to onset dates, the search window, and (per the control check in
`cause_or_cover.md`) whether the "stress" is distinctive at all.

## What this does — and does not — do to the argument

- **The literal claim needs revising.** "6–10 weeks to peak" is not supported;
  the honest figure is ~16 weeks and up. The draft should either restate the
  number or say precisely which lag it means (time-to-*material* vs time-to-peak).
- **The directional argument survives — arguably strengthened.** July 1914's
  window was **0.7 weeks**. Against peak lags of 16–37 weeks it is *more* obviously
  too short, not less: whatever the exact clock, five days is a fraction of it.
- **But the fast "material" onsets are the real caveat.** In two crises stress
  became material in ~10 days. That is still longer than July 1914's five, but it
  means the brake did not always need "weeks" — so the mechanism's strong form
  ("finance needed 6–10 weeks and never had it") is not what the data support; the
  defensible form is narrower: *peak* stress took months, and July 1914 truncated
  the process almost at t0.

## Caveats (real, and they cut both ways)

- **Provisional event spec.** Onsets and the binding-power→series mapping are the
  `crisis_lag` defaults, flagged as provisional. Peaks are sensitive to them.
- **Confounded series.** Morocco_1905→`russia` is contaminated by the
  Russo-Japanese war and the 1905 revolution — the July-1905 Russian-spread peak
  is not cleanly a Morocco signal. Balkans→Austria peaking in June 1913 (37 wk)
  reflects sustained war-and-mobilisation strain across two Balkan wars, not a
  single onset.
- **Contaminated benchmark.** These spreads are `country − British consol`, but
  the UK itself moves (Agadir involvement; the 1909 naval/budget crisis; the
  July-1914 liquidity flight — see [`uk_benchmark_check.md`](uk_benchmark_check.md)).
  Re-benchmarking to the neutral Dutch yield leaves most lags unchanged but
  collapses **Morocco 16 wk → 3 wk** — so prefer the Dutch-benchmarked reading
  where the two disagree.
- **Peak over a long window can catch non-crisis drift.** The `material` measure
  is more onset-local but variance-sensitive (see the package README).

## Reproduce

```bash
cd crisis_lag
python build_nw_spreads.py ../neal_weidenmier/data/longtermbonds.xls data/nw_spreads_long.csv
crisis-lag run data/nw_spreads_long.csv                 # peak measure (headline)
crisis-lag run data/nw_spreads_long.csv --measure material
```

> **Instrument matters (see [`money_market_vs_bonds.md`](money_market_vs_bonds.md)).**
> These lags are on long *bonds* — a solvency proxy. Re-run on **commercial paper**
> (money-market rates), the instrument the brake actually runs through, the stress
> arrives faster: Austria is abnormal within ~13 weeks on the money market vs only
> ~38 on bonds. So part of the "16–37 week" bond lag is the slowness of the *bond*
> instrument, not the transmission — which pulls the honest figure back toward the
> draft's 6–10 for the clearest case.

**Bottom line:** run on the data we have, a single "6–10 weeks" is not robustly
recovered — peak lags run 16–37 weeks while material-onset lags run 1–15 — so the
draft should say *which* lag it means, and on *which* instrument (bonds vs
commercial paper), rather than assert one figure throughout.
This doesn't rescue July 1914 for the sceptic either: 0.7 weeks is shorter than
every measured lag on both operationalizations. The defensible claim is the
directional one (July 1914 truncated the process almost at t0), stated with the
lag's real spread and confounds (provisional onsets; Morocco→russia and the 1905
revolution) on the table, not a point estimate.
