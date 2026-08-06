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

## Result — differentiated, and it does not support pure "cover"

| crisis (climbing-down power) | own bonds material *before* climb-down? | reading |
|---|---|---|
| **Bosnia 1909 (Russia, Kokovtsov)** | **Yes**, 162 days before — both measures | finance-as-constraint consistent |
| **Balkans 1912–13 (Austria, Biliński)** | **Yes**, 224 days before — both measures | finance-as-constraint consistent |
| **Agadir 1911 (Germany)** | **Yes on yield** (71 days, the 1911 bourse panic); **no on spread** (consols sold off too) | consistent on the affordability measure |
| **Morocco 1905 (France, Rouvier)** | **No** on France's own yield; spread "material" only degenerately, at onset | France's *own* finances were **not** the binding constraint |

No crisis shows the refuting pattern (stress only *after* the climb-down), so the
data does **not** support the pure "decoration" thesis. But two honest
qualifications:

- **Agadir is measure-dependent.** Germany's *absolute* borrowing cost spiked in
  Aug–Sept 1911 (the classic finance-forced-settlement case), but the *spread*
  over British consols did not — because consols sold off with it. The
  finance-as-cause reading rides on using the affordability level, not the spread.
- **Morocco 1905 is the case that leans toward the objection — and the book knows
  it.** France's own yield shows no material stress; France was a creditor power.
  Delcassé fell over **diplomatic isolation** (Britain's commitment uncertain,
  Russia crippled by Japan and revolution), not French insolvency. The book's own
  mapping puts the binding constraint not in French finances but in **Russia's
  collapse** — an alliance-transmission mechanism, not "France could not pay." So
  for *Rouvier specifically*, finance-as-direct-cause is the weakest, and the
  fiscal-justification-as-cover worry is most alive.

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

**Bottom line.** The market data is *consistent* with finance as a binding
constraint in three of four crises and offers no support for pure cover — but it
is silent on intent, and in the one case built on a named minister's own solvency
(Rouvier/France 1905) it actively fails to find French financial stress. Whether
the fiscal argument was cause or cover is, as the objection says, an archival
question; this test says only where the archives are most and least likely to
vindicate it.

## Reproduce

```bash
cd crisis_lag && python cause_or_cover.py     # both measures, all four crises
```

Climb-down dates and the climbing-down-power series are documented, debatable
assumptions in `cause_or_cover.py` (`CLIMB_DOWNS`); the Morocco→France and 1905
Russian-revolution confounds are real. This is a timing check, not a proof of
motive.
