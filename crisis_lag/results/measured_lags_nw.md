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

## The measured lag does **not** support the 6–10 week clock

- **Peak-stress lag is 16–37 weeks, not 6–10** — roughly **2–4× the asserted
  figure**, 0 of 4 comparators in the band. As a literal number, "6–10 weeks" is
  not what the sovereign spreads show; the peaks come much later. Robust to the
  benchmark: raw country yields (no consol subtraction) give the same 16–37 week
  peaks (`data/nw_yields_long.csv`).
- **"Material" onset is bimodal and often fast:** stress first crosses z>2 in
  ~1.4 weeks in Bosnia and the Balkans, but 8–15 weeks in Morocco/Agadir. So
  *significant* stress can arrive within days, even though the *peak* is months
  out.

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
- **Peak over a long window can catch non-crisis drift.** The `material` measure
  is more onset-local but variance-sensitive (see the package README).

## Reproduce

```bash
cd crisis_lag
python build_nw_spreads.py ../neal_weidenmier/data/longtermbonds.xls data/nw_spreads_long.csv
crisis-lag run data/nw_spreads_long.csv                 # peak measure (headline)
crisis-lag run data/nw_spreads_long.csv --measure material
```

**Bottom line:** run on the data we have, the 6–10 week transmission lag is *not*
corroborated — peak lags are 2–4× longer. That doesn't rescue July 1914 for the
sceptic (0.7 weeks is dwarfed by any of these lags), but the specific number in
the draft is wrong, and the mechanism should be stated as "peak stress took
months; 1914 cut it off at the start," with the fast material-onset cases
(Bosnia, Balkans ~1.4 wk) acknowledged rather than buried.
