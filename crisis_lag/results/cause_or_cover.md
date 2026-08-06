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

| crisis (power) | raw z>2 lead | survives controls? | reading |
|---|---|---|---|
| **Bosnia (Russia, Kokovtsov)** | 162 d | **Not robustly.** Only a small onset blip; 1908 spread (1.52) sits *below* calm 1906–07 (2.0) on a declining trend | weak / not distinctive — but *not* a clean refutation (see limits) |
| **Morocco (France, Rouvier)** | none / degenerate | **No.** France's own yield never crosses; no stress on either measure | France's finances were **not** the constraint (the firmest read) |
| **Agadir (Germany)** | 71 d (yield) | **Weakly.** +0.12 above 1909–10, but on a rising secular trend | modest, measure-dependent |
| **Balkans (Austria, Biliński)** | 224 d | **Yes on yield** (clears clean controls); *not* on the spread (1907 higher) | the strongest case — but **slow-building** (peak 1913) and measure-dependent |

**So the earlier "consistent in 3 of 4" is withdrawn** — but the corrected reading
is *weak and mixed*, not the opposite verdict. After controls, only **Austria**
shows even a plausibly distinctive own-market stress, and even it builds over the
whole long crisis rather than pressing *before* the decision; Russia's is a small
blip swamped by its post-1905 recovery; France's never existed; Germany's is small
and secular-trend-confounded.

**Limits of the control check itself (why this is suggestive, not decisive).**
There are only ~4 clean control years (1904, 1906, 1907, 1910), and each carries
its own disturbances — the 1907 global panic, the 1906 Algeciras aftermath and the
large 1906 Russian loan — so the "calm" baseline is not clean. These spreads also
carry strong secular trends (Russia's post-1905 recovery, Austria's U-shape), which
a level comparison conflates with crisis effects. With four confounded crises and
provisional onsets, the whole exercise is **underpowered in both directions**: it
undercuts the strong finance-as-cause reading without positively establishing its
negation.

Two things this does establish, both honest:
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

**Bottom line.** After controls, the market data supports finance-as-cause far
more weakly than the raw z>2 leads suggested: **one** clean distinctive case
(Austria, and slow-building), one weak/measure-dependent (Germany), and **two**
that show no distinctive own-market stress at all (Russia, France). It still
offers no positive support for *pure* cover (no "stress only after"), but it does
not vindicate the fiscal architecture either — and at Rouvier/France 1905 it
leans toward the objection. Whether each fiscal argument was cause or cover is, as
the objection says, an archival question; this test now says the archives have
*more* to do than the timing leads implied, and are least likely to vindicate the
French case.

## Reproduce

```bash
cd crisis_lag && python cause_or_cover.py     # both measures, all four crises
```

Climb-down dates and the climbing-down-power series are documented, debatable
assumptions in `cause_or_cover.py` (`CLIMB_DOWNS`); the Morocco→France and 1905
Russian-revolution confounds are real. This is a timing check, not a proof of
motive.
