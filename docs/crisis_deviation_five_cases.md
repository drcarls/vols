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

## Detrended — remove the cyclical level, and the war signals shrink to modest

Re-running with `--detrend` (centre each year's window at its own mean, so only the
within-window *shape* is compared) strips out the rate-level confound. Peak tightening
above own norm, detrended:

| Crisis | Detrended peaks | Verdict |
|---|---|---|
| Algeciras 1906 | Berlin **+0.52** (17 Mar), Paris +0.37, London +0.33 | a small Berlin-led bump survives at the conference climax |
| Tripolitania 1912 | Genoa +0.64, Berlin +0.72, Vienna +0.62 — **peaks scattered** (Feb, Mar, May) | not synchronized → stays inconclusive |
| Second Balkan 1913 | London +0.64, Berlin +0.38, Paris +0.25, Vienna +0.16 — peaks at the onset week | timing survives, **magnitude collapses** (raw +2.3 was the 1913 level) |
| Agadir 1911 (clean baselines) | Berlin +0.64 & Paris +0.60, both 30 Sep | the two protagonists co-move at the climax |

The headline: **once the cyclical level is removed, every pre-war money-market signal is
modest — roughly +0.3 to +0.7 points.** None is a dramatic squeeze; the large raw numbers
were the business cycle. What survives is *timing* (synchronization at the event week),
not magnitude — consistent with the spot-vs-to-arrive reversal, where the war component
was likewise small once the quarter-end seasonal was controlled.

## Press check — the Second Balkan "spike" was the semester-end, not the war

The detrended Second Balkan signal peaks at 28 Jun / 5 Jul — but so does the **30 June
semester-end liquidation**. The contemporary press settles which it was. *Le Temps*,
Paris, **30 June 1913**, at the war's onset:

> *"La liquidation se passe dans les conditions prévues; l'argent, très abondant en face
> de positions peu nombreuses à reporter, doit se contenter de taux modérés… la
> spéculation accueille cette constatation avec calme et même indifférence."*

Paris was **calm and indifferent** — money *abundant*, report rate ~2%, and the market met
the news with "indifférence." (Vienna's detrended signal was likewise tiny, +0.16; NFP
carried Balkan war news but no Vienna squeeze.) So the late-June bump was the
**semester-end settlement**, not the Second Balkan War. The great-power money market
**ignored** it — because, unlike the First Balkan War's winter crisis of 1912 (the
Austro-Russian mobilization scare, which *did* tighten Vienna/Berlin and run the savings
banks), the Second Balkan War was a **localized** Balkan conflict that never threatened a
general war.

## The pattern

After detrending and the press check, the crises sort by whether they threatened a
**general** (great-power) war — not by diplomatic temperature, and not by whether a war
was actually being fought:

- **Ignored — no general-war threat:** Tangier 1905 and Bosnia 1908–09 (serious scares
  that stayed diplomatic; money easy), and — the surprise — the **Second Balkan War
  1913** (a *localized* Balkan war; Paris explicitly *"calme et indifférence"*). A war
  being fought did not move the great-power money market when it stayed contained.
- **Priced, but modestly:** **Agadir 1911** (Berlin + Paris co-moving ~+0.6 detrended at
  the 30 Sep climax) and the **First Balkan winter crisis 1912** (the Austro-Russian
  mobilization scare — Vienna/Berlin tightened, savings-bank runs; see
  `continental_press_warscares.md`). These are the episodes that genuinely risked a
  general war, and they are the ones the money market reacted to — though even here the
  reaction is small once the cycle is removed.
- **Cyclically confounded:** Algeciras 1906 (a small Berlin bump survives) and
  Tripolitania 1912 (scattered) — suggestive at most.
- **1914:** priced at nothing until it arrived.

That is the paper's thesis, sharpened by the whole run and by controlling properly: the
money market discriminated by the **probability of a general war**, not by war as such or
by diplomatic noise — it ignored localized wars (Second Balkan) and pure scares (Bosnia)
alike, and stirred only for the crises that could have gone general (Agadir, the First
Balkan winter, 1914). And the war component it did price was **modest** — the dramatic
raw moves were the business cycle.

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
