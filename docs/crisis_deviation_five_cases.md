# The five pre-war crises through the seasonal-deviation test

Running `war_premia/crisis_deviation.py` — each city's money rate vs its **own** seasonal
baseline — across the five candidate crises. Descriptive; Neal–Weidenmier weekly rates.

**Read this caveat first.** The test compares a crisis year's window to baseline years'
same window. When the crisis year's **cyclical rate level** differs from the baselines'
(e.g. 1912–13 were tight-money years; 1908–09 were the post-1907-panic easing), the
deviation conflates the crisis with that level. Clean baselines that *bracket* the crisis
year cyclically exist for Agadir 1911 (→ its result is trustworthy) but **not** for the
1912–13 cluster (every nearby year is itself a crisis or a different regime). So for the
crowded years, trust **synchronized timing** (all cities peaking in the event week) over
absolute magnitude, and read the confounded cases as suggestive, not measured.

## Results (peak tightening above each city's own seasonal norm)

| Crisis (window) | Signal | What the test shows |
|---|---|---|
| **1. First Moroccan — Tangier, spring–summer 1905** | **none** | Paris +0.02, Berlin −0.22, London −0.06, Vienna +0.39 — all inside baseline noise, mostly *below* norm. The Tangier phase was a diplomatic crisis (resolved by Delcassé's fall, June 1905) with **no money-market bite**. |
| **1′. First Moroccan — Algeciras conference, winter 1906** | **moderate, Berlin-led** | Berlin **+1.16** (17 Mar), Vienna +1.08, London +0.81, Paris +0.59, peaking at the Feb–Mar 1906 conference near-breakdown. Real tightening — but **confounded** by the general pre-1907 monetary tightening, so partly cyclical. |
| **2. Bosnian annexation, autumn 1908 & spring-1909 climax** | **none (null)** | Every city *below* its norm — autumn 1908 (Vienna −0.52, Berlin −0.66, London −1.12) and at the Mar-1909 ultimatum climax (Vienna −0.58, Berlin −1.22). No tightening anywhere. Money was easy (post-1907 recovery), and the Bosnian scare left **no money-market mark** — matching Lansburgh's silence on it. |
| **3. Italo-Turkish / Tripolitania, 1912** | **confounded / inconclusive** | Large positives (Genoa +1.92, Vienna +1.62, Berlin +1.42) but the baselines (1908–10, easy) sit a whole cyclical regime below tight-1912, so the level inflates everything. Genoa (Italy, the belligerent) *leading* is a weak hint; not cleanly attributable to the war. |
| **4. Second Balkan War, summer 1913** | **strong, synchronized** | London +2.44, Vienna +2.34, Berlin +2.16, Paris +1.87 — **all peaking in the same two weeks (28 Jun / 5 Jul 1913), the war's onset.** The synchronized spike at the event week is a genuine event effect (a mere level shift would be flat-high, not peaked), though the 1913 stringency inflates the absolute size. |
| **5. July 1914 — pre-Sarajevo only** | **no anticipation** | Peaks fall in **January** (New York +2.31, Amsterdam +1.88, cyclical year-open), and by June every market is at/below norm (Berlin −1.34 on 13 Jun). No war was priced approaching Sarajevo. *The outbreak itself is beyond the data — the NW weekly series ends 1914-06-27* (covered instead by the Chronicle, Lansburgh, and the NFP → 8% Vienna). |

## The pattern

Ranked by money-market bite, the pre-war crises sort cleanly — and not by diplomatic
temperature:

- **Left no money-market mark:** Tangier 1905, Bosnia 1908–09. Both were serious *war
  scares* that stayed diplomatic; money stayed easy.
- **A real, timed money-market event:** the **Second Balkan War** (Jun–Jul 1913,
  synchronized onset spike) and **Agadir** (autumn 1911, Berlin the idiosyncratic mover —
  though that turned out to be largely the quarter-end, see `chapter3_digest_for_handoff.md`).
- **Confounded by the cyclical regime:** Algeciras 1906 (pre-1907 tightening) and
  Tripolitania 1912 (tight-year vs easy baselines) — suggestive, not clean.
- **1914:** priced at nothing until it arrived.

This is the paper's thesis quantified across the whole run: the pre-war crises that
*"cried war"* mostly did **not** move the money market — until the ones that actually
tipped toward general war (the Balkan onset, and then 1914) did.

## Reproduce

```bash
cd war_premia
python crisis_deviation.py --treatment 1906 --baselines 1903,1904,1908,1909 \
    --window 01-01:04-30 --cities paris_openmkt,berlin_openmkt,vienna_openmkt,london_trade3mo
python crisis_deviation.py --treatment 1913 --baselines 1909,1910,1911,1912 \
    --window 06-01:08-31 --cities vienna_openmkt,berlin_openmkt,paris_openmkt,london_trade3mo,genoa_openmkt
# ...and the other three cases (see the table windows).
```

All figures are from Neal–Weidenmier weekly rates; verify anything surprising against the
series and the contemporary press before it enters the manuscript.
