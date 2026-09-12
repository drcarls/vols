# The §6 counterfactual: verified, and stronger than the memo claimed

**Date:** 2026-09-12 · Branch `claude/walmart-milk-pricing-sc-m7zc99`

**Data — county universe, not a Walmart subsample.** USDA's own county-level table
(`DairyFMMO_USDADifferentialsCurrentvsProposedforFD.xlsx`, published on the AMS national hearing
page) joined by FIPS to Census ACS 2023 table B03002 via Census Reporter.
**3,100 of 3,109 counties matched, covering 329,117,050 people** — 12.0% Black, 57.5% White
non-Hispanic.

**Headline: the memo's central arithmetic is exactly right, and a revenue-neutral alternative
would have removed the entire widening.**

---

## 1. The memo's claim, independently replicated

Person-weighted mean Class I differential:

| Schedule | Black-weighted | White-weighted | Gap ($/cwt) | **Gap (¢/gal)** |
|---|---|---|---|---|
| **Current** (pre-2025) | $3.1398 | $2.6969 | $0.4429 | **3.81¢** |
| **Adopted** (2025 Final Decision) | $4.6578 | $4.0076 | $0.6502 | **5.59¢** |

The memo states the amendment widened the person-weighted gap **"from +3.8¢ to +5.6¢/gallon."**
Computed independently from USDA's table and Census counties: **3.81¢ → 5.59¢.** An exact match
to two significant figures.

**The gap widened by 1.78¢, a 47% increase.**

The amendment's *increase* is itself racially graded. Person-weighted, Black communities received
an increase of **13.05¢/gal** against **11.27¢/gal** for White communities. Regressing the
per-county change on %Black, population-weighted:

> **+0.0202 $/cwt per percentage point (t = +26.61)** = +0.174¢/gal per point; **+5.20¢ across a
> 30-point %Black gap.**

## 2. The gap was built in two discrete agency actions

| Schedule | Gap (¢/gal) | Added |
|---|---|---|
| 2000 base differentials (Federal Order Reform) | **2.91¢** | — |
| + 2008 adjustment to orders 5, 6 & 7 *(Appalachian, Florida, Southeast)* | **3.81¢** | **+0.90¢** |
| + 2025 amendment | **5.59¢** | **+1.78¢** |

The gap has nearly doubled since 2000, and **not through drift — through two separate
rulemakings**, each of which raised differentials disproportionately where Black Americans live.
The 2008 action applied *only to the three southeastern orders*: Black-weighted +$0.2631/cwt
against White-weighted +$0.1588. The final rule confirms this history: *"Current Class I
differential levels were implemented January 1, 2000, with updates to the differentials in the
three southeastern orders taking effect May 1, 2008."*

This matters legally: it converts a single-rule challenge into a pattern across two actions, and
the 2008 action has its own record.

## 3. Revenue-neutral alternatives

All three hold the population-weighted aggregate increase at the adopted **$1.2716/cwt
(10.93¢/gal)** and redistribute it. Arithmetic checked: each schedule's mean increase equals the
adopted one to four decimals.

| Schedule | Gap (¢/gal) | vs adopted |
|---|---|---|
| Adopted (2025 Final Decision) | 5.59¢ | — |
| **(1) Flat national increase** | **3.81¢** | **−1.78¢** |
| (2) Increase proportional to current differential | 5.55¢ | −0.04¢ |
| **(3) Cap each increase at the mean, redistribute the excess** | **4.01¢** | **−1.58¢** |

**A flat increase of identical total size would have left the racial gap exactly where it was.**
Capping each county's increase at the national mean and redistributing the remainder removes
**89% of the widening**, also at no aggregate cost.

**The memo's "~20% of the gap is removable" is conservative.** On these constructions,
1.78¢ of the 5.59¢ gap — **32% of the total, 100% of the 2025 widening** — is removable at
constant aggregate cost.

Option (2) is instructive by failing: scaling the *existing* differentials proportionally barely
helps, because the pre-2025 surface is already racially graded. Only changing the *distribution of
the increase* moves the number.

## 4. What this does not establish — and it is the important part

**I have not verified the specific counterfactual the memo posits.** Its claim is that the gap
shrinks if the increase tracks *USDA's own cost surface* — the USDSS model. That version is
legally much stronger than mine, because it cannot be answered with "this is geography": USDA's
model *is* geography, so a deviation from it is not.

I could not obtain the USDSS county values. They were entered as hearing exhibits (the *"May and
October 2021 USDSS model results"*) and are not among the files published on the AMS hearing page.
**Getting them is the highest-value remaining task.** They are in the record and therefore
obtainable.

**Three further limitations, stated plainly:**

1. **"Revenue-neutral" here is population-weighted, not volume-weighted.** USDA's $4.01bn figure
   weights by actual Class I volume per order (REIA Table 1). Per-capita fluid consumption varies
   regionally, so my aggregate is a proxy. The direction and rough magnitude are robust; the exact
   figure would shift on proper volume weights, and REIA Table 1 makes that refinement possible.
2. **A flat increase defeats the rule's stated purpose.** Location-specific differentials exist to
   reimburse transportation and incentivise milk movement. USDA would say — correctly — that a
   uniform increase sends no locational signal. **Counterfactual (3) is the defensible one**: it
   preserves the geographic slope up to the mean and removes 89% of the widening.
3. **This is incidence, not intent.** Nothing here suggests anyone set out to charge Black
   communities more. The documented mechanism (§5) is a producer trade association adjusting a
   cost model using "member knowledge."

## 5. The mechanism, in USDA's own words

From the Final Decision (89 Fed. Reg. 95,xxx, Dec. 2, 2024), which shows the adopted values are
**not** the model's output:

> *"Proposal 19 generally contained higher proposed differentials than the USDSS model average,
> **with greater increases moving northwest to southeast** to incentivize milk to move where
> needed."*

> *"the committee recommended **more slope than the USDSS model** by reducing the differential
> increases in the milk surplus areas of Michigan and **increasing the slope when moving to the
> south and east**."*

> *"the Florida differentials contained in Proposal 19 are similar to the averages of the May and
> October 2021 USDSS model results **but were adjusted to preserve current competitive
> relationships**."*

> *"MIG also provided specific comments questioning the Department's proposed Class I
> differentials in certain Texas and New Mexico counties **where the model suggested a Class I
> differential lower than current levels, but the Department proposed an increase**."*

And a methodological admission that matters:

> *"while the model results entered into evidence give estimates for the 3,108 counties in the
> contiguous United States, **the model only produces estimates for 663 demand locations.** The
> model then uses a **Kriging process** which interpolates estimates for the counties between the
> demand locations."*

So **2,445 of 3,108 county values are spatial interpolation, not model output** — and the
schedule actually adopted was proposed by the National Milk Producers Federation and adjusted by
"member knowledge," with the adjustments running *"northwest to southeast."*

## 6. Where the argument now stands

1. USDA quantified a **$4.01bn** transfer and declined to model its incidence, citing the
   county-level differentials (`reia_audit.md`).
2. The adopted schedule departs from USDA's own cost model, by design, **with greater increases
   moving toward the south and east** (§5).
3. That schedule widened the person-weighted racial gap **47%, from 3.81¢ to 5.59¢** (§1) — the
   third such widening since 2000 (§2).
4. **A revenue-neutral alternative would have removed all of the widening; a slope-preserving one
   removes 89%** (§3).
5. A represented party objected on the record that the cost falls on WIC and SNAP participants
   (`docket_audit.md`).
6. USDA certified no civil rights impact in three sentences, never using the word "consumer"
   (`cria_audit.md`).

Element 4 is the less-discriminatory-alternative element, and it is now quantified rather than
asserted. ***Block* remains the vehicle problem** — review of milk marketing orders is confined
to handlers, 467 U.S. 340 (1984).

## Reproduction

`analysis/counterfactual.py`. Inputs are public: USDA's county table from the AMS hearing page,
and ACS B03002 by county via the Census Reporter API (the Census Bureau's own API now requires a
key; Census Reporter does not).

---

# Addendum: the alternative was on the record, and USDA adopted the most graded of four

**Added 2026-09-12**, after retrieving the two county-level schedules filed at the hearing:
*Appendix A — National Milk Producers Federation Proposed Class I Differentials* and
*Appendix B — Milk Innovation Group Proposed Class I Differentials*, both published on the AMS
national hearing page. Parsed to **2,784 counties matched across all four schedules plus Census
demographics, covering 304,615,782 people.**

This supersedes §3's constructed counterfactuals with something far better: **alternatives that
were actually before the agency.**

## A. MIG's proposal is a uniform cut — one number, every county

Across all 2,960 counties in Appendix B, the change from the current base §1000.52 differential
is **exactly −$1.60**. Not a distribution, a single value. MIG proposed lowering the level and
**leaving the distributional shape alone** — specifically the pre-2008 base surface, since MIG
quotes the base differential rather than the effective one (verified: MIG's "current" differs
from USDA's effective by exactly the FO 5/6/7 adjustment; NMPF's matches USDA's effective in
2,783 of 2,784 counties).

NMPF's proposal, by contrast, ranges from **+$0.25 to +$2.70** across 47 distinct values.

## B. Racial gap under each schedule that was before the agency

| Schedule | Mean level $/cwt | **Gap ¢/gal** |
|---|---|---|
| **MIG proposal** (Appendix B) | $1.0032 | **2.62¢** |
| Current effective (pre-2025) | $2.7585 | 3.36¢ |
| **NMPF proposal** (Appendix A) | $4.2604 | **4.60¢** |
| **USDA adopted** (Final Decision) | $4.0476 | **5.05¢** |

Holding the national mean level identical at USDA's adopted $4.0476 — a uniform shift cannot
change a difference, so each row is purely that schedule's distributional shape:

| Shape, at a common national level | **Gap ¢/gal** |
|---|---|
| MIG shape | **2.62¢** |
| Current shape | 3.36¢ |
| NMPF shape | 4.60¢ |
| **USDA adopted** | **5.05¢** |

**USDA adopted the most racially graded of the four options on the table** — more graded than the
producer trade association's own proposal, more than the status quo, and **93% more than MIG's.
At an identical national price level, MIG's schedule would have cut the gap 48%.**

## C. USDA's own departures from NMPF were graded too

USDA did not simply take NMPF's schedule. It went **above** NMPF in 419 counties and **below** in
2,153, lowering the national mean from $4.2604 to $4.0476. But the cuts were not distributed
neutrally:

> **USDA's deviation from NMPF's proposal, regressed on county %Black, population-weighted:
> +0.00477 $/cwt per percentage point (t = +12.08).**

USDA cut less where the Black share was higher. That is why its gap (5.05¢) exceeds NMPF's
(4.60¢) despite a lower overall level.

## D. Why this is the strongest form of the argument

A less-discriminatory-alternative element normally requires the challenger to construct one and
defend its feasibility. Here it does not:

1. **The alternative was filed.** MIG's Appendix B is in the record, county by county.
2. **It is administratively trivial.** A single uniform adjustment — no county-by-county judgment,
   no model, no interpolation.
3. **The distributional comparison is clean.** Because MIG's proposal is a constant shift, the
   level and the distribution separate exactly. USDA can defend its *level* on producer-return
   grounds under the AMAA. It cannot defend its *distribution* on those grounds, because a
   different distribution at the same level was available.
4. **USDA went further than the party that asked.** The agency's own adjustments to NMPF's
   proposal were themselves racially graded at t = 12.

## E. Limits — and one is important

- **MIG did not propose the rescaled version.** Its actual filing cuts the mean level from $2.76
  to $1.00, a very large reduction in producer revenue that USDA could reject on statutory
  grounds and almost certainly would. **The rescaling is my analytical device** for separating
  level from distribution. It is the right device for a disparate-impact analysis — which
  concerns distribution — but it is not a schedule anyone submitted.
- **Coverage.** 2,784 counties here against 3,100 in §1, because ~10% of rows were lost to PDF
  text extraction. On this subset the adopted-vs-current widening reads **3.36¢ → 5.05¢** against
  **3.81¢ → 5.59¢** on the fuller set. Same direction, magnitudes ~12% smaller. The fuller
  figures in §1 are the ones to quote; these are for comparing schedules to each other.
- **Still not the USDSS comparison.** The model's county values remain unobtained — they are
  hearing exhibits and are not among the 77 files published on the AMS page. MIG's schedule is a
  *better* legal instrument than a reconstructed USDSS, but USDSS would answer the "this is
  geography" defence more directly, since it is USDA's own cost surface.

## F. The chain, restated

1. USDA quantified a **$4.01bn** transfer and declined to model its incidence (`reia_audit.md`).
2. Four county-level schedules were before it. **It adopted the most racially graded** (§B).
3. Its own departures from the producer proposal rose with %Black, **t = 12.08** (§C).
4. The adopted schedule widened the person-weighted gap **47%, 3.81¢ → 5.59¢** (§1) — the second
   such widening since 2000 (§2).
5. **A filed alternative would have cut the gap 48% at the same national level** (§B).
6. A represented party objected that the cost lands on WIC and SNAP participants
   (`docket_audit.md`).
7. USDA certified no civil rights impact in three sentences, never using the word "consumer"
   (`cria_audit.md`).

***Block* still governs the vehicle** — 467 U.S. 340 (1984) confines review of milk marketing
orders to handlers. Note, though, that **MIG's members are handlers**, they filed the alternative,
and they objected on consumer-incidence grounds. The party with standing and the party with the
better schedule are the same party.

## Reproduction

`analysis/counterfactual_schedules.py`.
