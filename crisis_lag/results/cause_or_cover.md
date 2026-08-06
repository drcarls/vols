# Cause or cover — what the market data can and cannot say

**The objection (unsettled).** If Rouvier, Kokovtsov and Biliński produced
*fiscal* justifications for climb-downs actually decided on military and
diplomatic grounds, the financial architecture is decoration. **Market data
cannot settle that.** Intent — whether a fiscal argument *drove* a decision or
*dressed* one already taken — lives in cabinet minutes and ministerial
correspondence, not in bond prices. Nothing below establishes motive.

**The one bounded, asymmetric handle it does give.** Was the climbing-down
power's *own* financial stress already **material** (first z>2 above a pre-onset
baseline in its sovereign spread / yield) at the moment it climbed down?

- **Material only *after* the climb-down** would *refute* finance-as-cause — the
  fiscal argument would have to be post-hoc. This the test can establish.
- **Material *before*** is *consistency*, never proof: a government can climb down
  on diplomatic grounds while its bonds happen to be stressed. Necessary, not
  sufficient.

So the test can partially refute, never confirm (`cause_or_cover.py`).

## The raw "material before" flags do not survive a control check

A first pass found each climbing-down power's bonds "material" (z>2) *before* the
concession — Russia 162 days before, Austria 224. **But those leads are long
enough to be suspicious, and they do not survive controls.** A z>2 crossing is
only crisis stress if the crisis-window level actually *exceeds* what the same
bond did in the same calendar window in **clean (non-crisis) years**; otherwise it
is a low-variance-baseline artifact riding a pre-existing level or trend. Checked
two ways — matched clean-year control windows, and the yearly-mean trend
(`cause_or_cover.py`):

**Yearly-mean spread (over British consols):**
```
russia:    1906 2.01  1907 2.00  1908 1.52  1909 1.24  1910 0.86  1911 0.73  1912 0.70
austria:   1910 0.64  1911 0.57  1912 0.56  1913 0.70  1914 1.00
```

This crude level check flagged Russia and Germany as weak/not-distinctive and
called only Austria genuine — but that check is itself confounded three ways (only
~4 "clean" control years, 1904/06/07/10, each with its own disturbance — the 1907
panic, the 1906 Algeciras aftermath and the big Russian loan — and strong secular
trends that a level comparison conflates with crisis effects). So it was too
dismissive. **Fix the control properly and the signal comes back.**

## The fixed control — neutral benchmark, change, null distribution

The event-study control removes all three confounds:

1. **Benchmark against a neutral creditor — the Dutch yield — not British
   consols** (a great-power asset that itself sold off for liquidity). This strips
   common global bond moves and Britain's own contamination.
2. **Measure the *change*** (max rise of the power-minus-Dutch spread over a
   window), not the level. This strips the secular trend.
3. **Compare that change to its distribution over *every* non-crisis window** — a
   real null, not a handful of hand-picked years — and read off a percentile.

**Percentile of the crisis-window rise (power − Dutch) vs all non-crisis windows:**

| crisis (power) | 90 d | 180 d | 270 d | reading |
|---|---|---|---|---|
| **Agadir (Germany)** | 49 | **93** | **90** | strong — the 1911 panic, building over months |
| **Bosnia (Russia, Kokovtsov)** | 68 | **85** | 78 | **real, moderate** — an above-normal rise, *not* an artifact |
| **Balkans (Austria, Biliński)** | 0 | 0 | **89** | holds, but **slow** — arrives in 1913, at the horizon it needed |
| **Morocco (France, Rouvier)** | 17 | 13 | 9 | **firm null** — France *below* normal, no stress |

Benchmarked against the Dutch neutral, each power whose own solvency was in
question (Germany, Russia, Austria) showed an abnormal rise and France none — which
looked like "largely holds for three of four."

> **Correction — it does not survive a *far* neutral (see
> [`neutral_robustness.md`](neutral_robustness.md)).** The Netherlands borders
> Germany and prices invasion risk; genuine far neutrals are the US, Sweden,
> Switzerland. Re-run against those, the per-country percentiles **scatter** (Russia
> 21–89, Germany 26–70, Austria 28–94 across neutrals) — the "three of four" was
> **Dutch-specific and is withdrawn.** With four confounded crises and small/noisy
> neutral markets the country-specific signal is at the noise floor. Only two
> things survive every neutral: **France was calm in the money market** (0–10th
> percentile everywhere → the 1905 constraint lay in the ally, Russia, not French
> finances), and **Austrian debt repriced through the Balkan Wars** (89–100th vs
> every bond neutral). Russia and Germany cannot be claimed per country from these
> bond/bill prices.

**Remaining limits (still real).** A single neutral (Dutch) and current-yield
proxies; the null windows overlap and are not independent, so the percentiles are
descriptive, not test p-values; Austria's signal is entirely horizon-dependent
(nothing at 90–180 d). And none of this touches intent — an above-normal bond
move is consistency with finance-as-constraint, still not proof that it *caused*
the climb-down rather than accompanying it.

Two things this establishes, both honest:
- **No crisis shows the refuting pattern** (stress *only after* the climb-down),
  so nothing positively supports pure "cover" either.
- **Morocco/Rouvier is where the objection is most alive.** France was a creditor
  power under no market stress; Delcassé fell over **diplomatic isolation**
  (Britain's commitment uncertain, Russia crippled by Japan and revolution). The
  book itself locates the constraint not in French finances but in **Russia's
  collapse** — an alliance mechanism, not "France could not pay." A fiscal
  justification there would be closest to decoration.

## What this leaves for the archives

The timing test narrows the question but cannot close it. For each minister the
decisive record is the same in form — does the fiscal argument *predate and
drive* the concession, or *postdate and dress* it?

- **Rouvier (France, 1905):** French cabinet papers and the Rouvier–Delcassé
  rupture (Conseil des ministres, 6 June 1905); French diplomatic documents
  (*Documents diplomatiques français*, 2e série). Did Treasury/Bourse concerns
  enter *before* Delcassé's fall, or was it Anglo-Russian exposure?
- **Kokovtsov (Russia, 1908–09):** Kokovtsov's own memoranda as finance minister
  and the Council of Ministers records; his memoir *Out of My Past*. Did he veto
  war on affordability grounds *before* the March 1909 acceptance?
- **Biliński (Austria-Hungary, 1912–13):** the k.u.k. Joint Finance Ministry
  papers (HHStA, Vienna) and the Common Ministerial Council protocols — did
  Biliński's cost objections shape the decision not to fight Serbia, or ratify it?
- **Germany (Agadir, 1911, and the July 1914 parallel):** the Reichsbank /
  Treasury records (BArch R 2, R 2501) and Zilch's monograph — see
  [`../../docs/july1914_mechanism_and_archival_test.md`](../../docs/july1914_mechanism_and_archival_test.md).

**Bottom line.** Properly controlled — neutral benchmark, change, null
distribution — the market data is **consistent with finance as a binding
constraint for the three powers whose own solvency was in question**: Germany
(~90th percentile), Russia (~80th), and Austria (~90th, but only at the long
horizon its two-winter crisis needed). **France (Morocco 1905) is the clean
exception** — no own-market stress at all, consistent with the book's own placing
of the 1905 constraint in Russia's collapse, not French finances. That is a
stronger reading than my over-corrected "weak/mixed," and a more disciplined one
than the first pass's raw z>2 leads. But it remains *consistency, not causation*,
and it is silent on intent. Whether each minister's fiscal argument **caused** the
climb-down or **dressed** it is, as the objection says, an archival question — the
sources named above — and the market data's contribution is only to say the
financial pressure was really there for Kokovtsov, Biliński and the Germans, and
really absent for Rouvier.

## Reproduce

```bash
cd crisis_lag && python cause_or_cover.py     # both measures, all four crises
```

Climb-down dates and the climbing-down-power series are documented, debatable
assumptions in `cause_or_cover.py` (`CLIMB_DOWNS`); the Morocco→France and 1905
Russian-revolution confounds are real. This is a timing check, not a proof of
motive.
