> **SUPERSEDED IN PART — read `reports/above_cost_regional.md` alongside this.** The
> national departure-from-cost regression in §3–4 below pools regions carrying opposite
> signs (the West is priced far below the cost surface, the South above it), so it
> understates the effect by construction. The regional decomposition shows USDA marked the
> South up 3.92¢/gal and the West down 6.58¢/gal against its own freight model, with no
> racial gradient inside any region. Everything else here stands.

# Is the Class I differential surface the transport-cost surface?

**Exhibit MIG-16A, admitted into the hearing record, makes the agency's central
defense testable for the first time. It largely survives.**

Reproduce: `python3 analysis/usdss.py`

---

## Why this test and not another

Every version of Finding A invites one answer: *the differential is a transport-cost
surface, and Black Americans happen to live in the milk-deficit South and the
coastal cities where milk is expensive to deliver. The gradient is geography, not
race.* Until now that answer could not be tested, because USDA's cost surface was
not in hand. `reports/counterfactual.md` §E recorded it as unobtainable: "those
county values are hearing exhibits and are not among the 77 files published on the
AMS page."

They are in the record. They were filed by the model's own author.

## Provenance

**Exhibit MIG-16A** — `FMMO_MIG_16A.xlsx`, 184 KB,
`ams.usda.gov/sites/default/files/media/FMMO_MIG_16A.pdf`→`.xlsx`. Titled, at
MIG-16 p. 13: *"Shadow Price Values for Class I, Class III, and Price Difference for
March, 2016, USDSS Model Run."* 3,085 counties × {state, county, FIPS, Class I
shadow price, Class III shadow price, difference}.

Sponsored by **Dr. Mark Stephenson** (Exhibit MIG-16), who testifies at p. 8 that he
and Dr. Charles Nicholson "are the current caretakers of the USDSS," and at p. 9
that AMS "has relied on this model to provide guidance into Class I differentials in
the past." **ADMITTED into evidence** — *Ruling: Record Exhibits*, AO Docket No.
23-J-0067, 22 March 2024, "Exhibits 1 through 74 were ADMITTED."

This is not a plaintiff's model. It is the government's cost model, filed by its
author, admitted without objection, and it is the same model family NMPF used to
build the schedule USDA adopted.

## Method: why no rescaling is needed

USDSS duals are *price relatives* with an arbitrary zero. MIG-16 p. 9: "There will
be one or more locations in the country where that value is $0.00." Only additive
shifts of such a surface are meaningful — its level carries no information.

That is not an obstacle here, because the statistic used throughout this engagement
— the person-weighted Black mean minus the person-weighted White mean — is *exactly
invariant* to an additive shift. Cost and regulatory surfaces are therefore compared
on the one scale they genuinely share: **distributional shape**. Levels are reported
but never differenced across surfaces.

Two readings of "the cost surface," both run, because the record supports both:

| reading | what MIG-16 says it is |
|---|---|
| **Class I dual** | what "AMS has only asked for" (p. 10) |
| **Class I − Class III** | the "'incentive' value or 'give up' charge for delivering milk to a fluid plant instead of a manufacturing plant" (p. 10) — the quantity a Class I differential is economically meant to cover |

Universe: 3,077 counties matched across MIG-16A, USDA's county table, and ACS 2023
B03002. Population 328,376,309; 12.0% Black, 57.5% White non-Hispanic; 48 states.

---

## Result 1 — the cost surface is itself racially graded

| surface | mean $/cwt | Black-wtd | White-wtd | **gap ¢/gal** |
|---|---|---|---|---|
| USDSS Class I dual | 3.639 | 4.092 | 3.548 | **4.68¢** |
| USDSS Class I − Class III | 0.031 | 0.399 | −0.074 | **4.06¢** |
| 2000 base differentials | 2.602 | 2.876 | 2.537 | 2.91¢ |
| current (pre-2025) | 2.773 | 3.140 | 2.696 | 3.82¢ |
| **adopted 2025** | 4.043 | 4.656 | 4.006 | **5.59¢** |

**This is the finding that matters, and it is not the one the theory wanted.** A
pure least-cost transport model, run on 2016 data by the model's own caretaker,
produces a Black–White gap of **4.68¢/gal** — *larger* than the 3.82¢ carried by the
differentials in force before 2025.

On this statistic the pre-2025 Class I differential surface was **less** racially
graded than least-cost dairy logistics would imply. The agency's geography defense
is not a rationalisation. For the schedule that stood from 2008 to 2025, it is
simply correct.

## Result 2 — 2025 crossed the cost surface, and the widening is all shape

The adopted schedule is the first to price **above** the cost surface in aggregate
incidence: 5.59¢ against 4.68¢, an excess of **0.91¢/gal** (16% of the adopted gap),
or **1.53¢** (27%) measured against the give-up charge.

Decomposing the 2025 widening:

| | Class I dual | Class I − III |
|---|---|---|
| current → cost surface (convergence) | +0.87¢ (49%) | +0.24¢ (14%) |
| cost surface → adopted (beyond cost) | **+0.91¢ (51%)** | **+1.53¢ (86%)** |
| total widening | +1.78¢ | +1.78¢ |

And note what the level did: the population-weighted mean differential rose $1.27/cwt,
from $2.773 to $4.043. Because the gap is shift-invariant, **none of that level
increase produced any of the widening.** All +1.78¢ came from re-sloping the surface.
USDA did not merely raise milk's regulated floor; it changed which places pay more
relative to which, and that re-sloping is the whole of the distributional effect.

The adopted surface tracks the cost surface closely — regressing adopted on the
Class I dual, population-weighted, gives **R² 0.73** (current: 0.59). Three quarters
of the surface is cost. The argument is only ever about the last quarter.

## Result 3 — inference, and where the claim stops

State-block permutation, 2,000 draws, demographics reassigned across whole states so
that within-state structure is preserved (counties in a state share a pricing zone
and a hauling network, so they are not independent observations — the same correction
that took Finding A's region-FE *t* from 13.29 to 2.17):

| surface | gap ¢/gal | perm *p* |
|---|---|---|
| current differentials | 3.82¢ | 0.052 |
| **adopted differentials** | **5.59¢** | **0.041** |
| USDSS Class I dual | 4.68¢ | 0.074 |
| USDSS Class I − III | 4.06¢ | 0.080 |
| **adopted minus cost (Class I dual)** | **0.91¢** | **0.289** |
| **adopted minus cost (Class I − III)** | **1.53¢** | **0.106** |

**The adopted schedule's gap is significant (p .041). The part of it that exceeds
the cost surface is not (p .289; p .106).**

Same conclusion from the gradient regressions. Slope of the departure-from-cost on
county %Black, person-weighted, SEs clustered on 48 states:

| | $/cwt per pt | *t* | leave-one-state-out *t* | perm *p* |
|---|---|---|---|---|
| vs Class I dual | +0.01316 | +1.66 | [+1.47, +1.78], 0/48 sign flips | 0.212 |
| vs Class I − III | +0.02015 | +2.09 | [+1.90, +3.26], 0/48 sign flips | 0.113 |

The sign is completely stable — no state's removal flips it, and the leave-one-out
range never approaches zero. But under honest inference neither reaches
conventional significance. **Point estimates consistently positive, never
significant** is the accurate summary, and it is the summary that should be given
to counsel.

## Result 4 — the mechanism, which is not what you would guess

The departure from cost, among the 25 largest counties:

| county | %Black | current | adopted | cost | departure |
|---|---|---|---|---|---|
| San Diego CA | 4.4 | 2.10 | 2.80 | 4.41 | **−1.61** |
| Orange CA | 1.5 | 2.10 | 2.80 | 4.30 | −1.50 |
| San Bernardino CA | 7.5 | 1.80 | 2.60 | 4.02 | −1.42 |
| Los Angeles CA | 7.4 | 2.10 | 2.80 | 4.14 | −1.34 |
| Clark NV | 11.5 | 2.00 | 2.60 | 3.73 | −1.13 |
| **Wayne MI (Detroit)** | **36.6** | 1.80 | 3.30 | 4.05 | **−0.75** |
| Maricopa AZ | 5.4 | 2.35 | 2.60 | 3.37 | −0.77 |
| **Cook IL (Chicago)** | **21.8** | 1.80 | 3.20 | 3.91 | **−0.71** |
| **Philadelphia PA** | **38.3** | 3.05 | 4.60 | 4.50 | **+0.10** |
| Middlesex MA | 4.7 | 3.25 | 5.10 | 4.26 | +0.84 |
| Palm Beach FL | 18.1 | 6.00 | 7.40 | 6.59 | +0.81 |
| Broward FL | 27.4 | 6.00 | 7.40 | 6.71 | +0.69 |
| Harris TX | 18.6 | 3.60 | 4.80 | 4.12 | +0.68 |
| Miami-Dade FL | 14.1 | 6.00 | 7.40 | 6.75 | +0.65 |
| Bexar TX | 7.4 | 3.45 | 4.30 | 3.72 | +0.58 |

The positive gradient is driven by a **California-versus-South-and-Northeast**
contrast, not by a Black/White contrast within metros. USDA prices the California
metros $1.30–1.60/cwt *below* what the cost model says milk is worth there, and
Texas, Florida and New England *above*. California is the least-Black of the large
metro blocs, so the racial gradient partly falls out of that one regional decision.

Two of the largest Black population centres in the country — Detroit (36.6% Black,
−$0.75) and Chicago (21.8%, −$0.71) — are priced **below** the cost surface, and
Philadelphia (38.3%) is within a dime of it. A theory that USDA marked up Black
metros does not survive contact with this table.

Where the gradient does live is the rural Black Belt: the 20 Blackest counties
average **+$0.567** departure against **+$0.157** for the 20 least-Black. Real, and
in the expected direction, but those are small-population counties, which is exactly
why the person-weighted aggregate lands at *p* .289.

---

## Result 5 — what the record says about how the surface was built

Independent of any statistic, **Exhibit NMPF-38** (`FMMO_NMPF_38.pdf`, amended)
describes, in NMPF's own words, a surface that was negotiated rather than computed:

- USDSS produced "a list of relative values for milk at specific locations" on May
  and October 2021 input data (p. 7).
- Because the collaborators "were local as opposed to global experts," NMPF "created
  a spine of nineteen strategically chosen anchor cities," from which "regional
  subgroups could branch out and discuss **increasing or decreasing the
  USDSS-generated Class I values** using knowledge of specific local challenges"
  (p. 7).
- Counties were then moved between zones **to equalise raw-product costs among
  competing Class I plants** — Allegheny County PA shifted from the $4.40 zone to
  $4.20 "because plants located in Allegheny County compete for Pittsburgh area
  business"; Clark County OH moved from $4.00 to $3.70 (pp. 14–15).
- "Differences for counties along the seams were resolved through discussions with
  staff representing the Northeast, Southeast, and Midwest Areas," and "some fine
  tuning was necessary" to produce "an explainable and contiguous Class I
  differential surface" (pp. 13–15).
- NMPF quantifies its own departures for the Mideast: of 406 counties, 18 (4%) more
  than $0.25 *above* USDSS (max +$0.40, central Kentucky) and 97 (24%) more than
  $0.25 *below* (max −$0.70, northern Michigan) (pp. 15–16).

So the surface USDA adopted is a cost model, adjusted by regional committees of milk
marketers, tuned to protect the competitive position of named Class I plants, and
smoothed for presentability. **That is a rulemaking-record fact, not a statistical
inference, and it does not depend on any *p*-value.** It is what makes "the
differential is just transport cost" an overstatement even though the cost surface
turns out to carry most of the gradient.

### Validation of Exhibit 16A against NMPF's description

NMPF-38's account is a partial check on whether the March 2016 run in 16A proxies
the 2021 run NMPF worked from. Comparing adopted 2025 against 16A, by state:

| state | n | mean departure | >$0.25 below | >$0.25 above |
|---|---|---|---|---|
| MI | 83 | −0.337 | 56 | 2 |
| IN | 92 | −0.238 | 51 | 2 |
| OH | 88 | −0.333 | 56 | 0 |
| KY | 120 | **+0.232** | 0 | 68 |
| WV | 55 | +0.074 | 0 | 3 |
| PA | 67 | +0.130 | 0 | 15 |

**Reproduces:** the sign pattern (Michigan, Indiana, Ohio below cost; Kentucky
above) and the rough magnitudes — largest Michigan downside −$0.77 against NMPF's
−$0.70, largest Kentucky upside +$0.53 against NMPF's +$0.40.

**Does not reproduce:** the county shares (51% of Mideast counties below cost by
>$0.25 here, against NMPF's 24%) and the within-Michigan geography — NMPF locates
the below-cost counties in *northern* Michigan, whereas 16A puts the largest
departures in the *southeast* (Monroe, Wayne, Washtenaw, Lenawee, Macomb, Oakland,
all −$0.69 to −$0.77).

Different run, different vintage, and NMPF was comparing its *proposal* while this
compares USDA's *adopted* schedule. **16A corroborates the direction and scale of
the departures NMPF described; it does not reproduce NMPF's figures and must not be
presented as doing so.**

---

## Limits

- **One month.** The 16A run is March 2016 alone. MIG-16 p. 9 says the model
  "represents a snapshot in time" and that a flush and a short month are normally run
  as a pair. Only one was filed. The seasonal counterpart is not in the record.
- **Wrong vintage.** The 2025 schedule was built on 2021 input data (NMPF-38 p. 7),
  not 2016. Some divergence is vintage, not method. This cuts one way only: vintage
  cannot manufacture a gradient in county %Black unless milk haulage costs themselves
  moved with racial composition between 2016 and 2021.
- **Above cost is not unlawful.** §1000.52 differentials are not required to equal a
  transport dual. The AMAA directs USDA to consider producer returns and orderly
  marketing as well. "Above the cost surface" is evidence about the rule's *stated*
  rationale, not a legal conclusion.
- **The 2021 Stephenson/Nicholson run itself** — the one NMPF actually worked from —
  is still not in hand. NMPF-38 quotes results from it but does not attach the county
  table. That is the remaining FOIA/discovery target, and it would replace every
  vintage caveat above.

## What this changes elsewhere in this repo

- `reports/counterfactual.md` §E — the open item ("USDSS county values remain
  unobtained") is **closed**, with the answer going partly against the memo.
- The 48% gap reduction from MIG's filed schedule (`reports/counterfactual.md`
  addendum) remains arithmetically correct but is now weaker as a
  less-discriminatory alternative: MIG's schedule is the current surface shifted down
  $1.60, so its shape carries a 3.82¢ gap — **below** what the cost surface implies.
  USDA could reject it as under-signalling location, and the record gives it grounds.
- The strongest surviving claims are the ones that never rested on the racial
  gradient of the departure: the CRIA's three sentences (`reports/cria_audit.md`), the
  $4.01bn transfer analysed without reference to anyone who pays it
  (`reports/reia_audit.md`), MIG's unanswered WIC/SNAP incidence comment
  (`reports/docket_audit.md`), and now the fact that **51%–86% of the distributional
  widening lies beyond the cost surface USDA's own model produced** — an APA
  failure-to-justify point that needs no *p*-value.

## Bottom line for counsel

The geography defense is largely right, and it should be assumed the government will
make it and win on it for the pre-2025 schedule. What the record will support is
narrower and better aimed:

1. The 2025 amendment is the first to price above the least-cost surface in
   aggregate incidence, by 0.91¢–1.53¢/gal.
2. The entire distributional widening is re-sloping, not the level increase the rule
   was justified by.
3. Half to six-sevenths of that widening has no support in USDA's own cost model.
4. The surface was hand-adjusted off that model by committees of regulated firms, to
   protect named plants' raw-product costs.
5. And USDA certified no civil-rights impact in three sentences without analysing
   consumers at all.

None of that requires the claim that the differential's racial gradient exceeds
chance — which, tested honestly, it does not.

---

## Published summary

The public NAACP summary (`reports/public_summary.html`, published as a private
Claude artifact) was updated to version 2 to carry this result, because version 1
stated in its footer that no audit had been performed of the rulemaking record, the
Civil Rights Impact Analysis, the 2025 amendment, or any alternative-schedule
counterfactual — all four of which have since been done — and answered the geography
rebuttal only with the weak within-region evidence.

Version 2 adds two sections: the cost-surface test (leading with the finding that
goes against the theory) and the administrative record. Its "next steps" list is
rewritten around what is actually still open, and the footer now carries the
vintage, single-month and "above cost is not unlawful" caveats. The document
contains no client names, credentials, or engagement history.
