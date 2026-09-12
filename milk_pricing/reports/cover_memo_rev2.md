# What needed correcting in the NAACP cover memo

**Date:** 2026-09-12 · Deliverable: `reports/Cover_memo_NAACP_rev2.docx`
**Input:** the September 2026 cover memo as sent to NAACP LDF (client-supplied).

Reproduce the new estimates: `python3 analysis/within_state_zones.py`, `python3 analysis/usdss.py`

---

## Three changes, two of which weaken the case

### 1. §9, the retail strand — withdrawn

The memo told counsel a milk-specific retail premium was *"robust in South Carolina and
Louisiana after a same-region control."* It is not. SC within postal region **t −1.56**, LA
**t +0.37**, NC and TX significantly negative; metropolitan Atlanta **−2.9¢, p 0.65** with power
to detect 12¢; twelve metros, none positive, pooled −0.0007 (t −0.88). This was the only
affirmative claim in the memo about a *named private company*, so it was the most exposed.

The memo also referenced *"deceptive-discount patterns at several retailers."* That was never
part of this analysis. The revision says so and expresses no view, rather than inheriting a
claim I cannot support.

### 2. §4a, new — the geography defence is largely correct, and the markup is regional

Exhibit MIG-16A (see `reports/usdss.md`) makes the cost-of-service defence testable. The
least-cost freight surface carries a **4.68¢** gap against **3.82¢** for the differentials in
force 2008–2025. The pre-2025 schedule was *less* racially graded than freight economics imply.
The memo had no answer to this objection beyond §2's "not a Southern artifact" argument, which
addresses a different question (whether the gradient is only the South) than the one the
government will actually ask (whether the gradient is cost).

### 3. §§2, 4, 7 — the *t*-statistics

The memo reported t = 66 (§2), 16 (§2 within-state), 14.0/13.5/9.0/9.3 (§4) and 20.4 (§7). All
treat each county or ZIP as independent. The Class I differential is a step function taking
**three to eleven distinct values per state**, so counties sharing a value are one observation.

Re-estimated on the memo's own universe (3,077 counties, person-weighted, adopted 2025):

| | coefficient | t unclustered | t clustered on state |
|---|---|---|---|
| raw | +0.0503/cwt per pt | +28.3 | **+5.60** |
| + state fixed effects | +0.0056/cwt per pt | +9.5 | **+2.63** |

So t = 66 is not reproducible even unclustered on this universe. **But the findings survive** —
both the raw and the within-state gradient remain conventionally significant. Two figures in §2
also needed correcting: the raw-to-within-state shrinkage is **nine-fold, not five-fold**, and
the between/within split is **95/5, not 92/8**.

§4, clustered on the differential zone (`analysis/within_state_zones.py`):

| state | counties | zones | coef $/cwt | t clustered | memo t |
|---|---|---|---|---|---|
| New York | 62 | 8 | +0.0493 | **+9.22** | 7.4 |
| Pennsylvania | 67 | 8 | +0.0135 | **+5.62** | 13.5 |
| Arkansas | 75 | 7 | +0.0169 | **+3.68** | 14.0 |
| Texas | 254 | 11 | +0.0444 | **+2.82** | 7.4 |
| Virginia | 110 | 6 | +0.0093 | **+2.49** | 9.0 |
| Alabama | 67 | 5 | +0.0052 | **+2.37** | 9.3 |
| South Carolina | 46 | 3 | +0.0050 | +1.52 | listed "yes" |
| Georgia | 159 | 4 | +0.0030 | +1.05 | listed "yes" |
| Mississippi | 82 | 6 | −0.0041 | −1.18 | — |

**Six states survive, not eight.** The memo's *"eight states, every t above 5"* is wrong twice:
only NY and PA exceed 5, and SC and GA fall below significance. Both were listed as "yes".

### 4. §7 — the alternative was measured against the wrong baseline

The memo measured the 2025 increase against USDA's *prior differential* as the cost baseline
(+$0.0157/cwt per point, t 20.4). §4a shows the prior differential was itself below cost, so
USDA's reply — the prior surface understated cost — is now supported by USDA's own filed model.
The memo anticipated that objection in a parenthetical; the new evidence confirms it.

The illustrative re-anchoring also fails, and this one matters because it was the memo's lead
example:

| | memo's nearest-supply estimate | USDSS at a common mean | adopted |
|---|---|---|---|
| Bronx, NY | ~$3.70 | **$4.91** | $5.10 |
| Philadelphia, PA | ~$2.90 | **$4.50** | $4.60 |
| Oneida, NY | "should be near $2.40" | **$3.66** | $3.90 |

Departures of **+$0.19 and +$0.10**, not $1.40 and $1.70 — an overstatement of roughly sevenfold
in the examples the section leads with. Distance to nearest production is not the cost of serving
a metro: the model must account for plant capacity and assembly that upstate New York cannot
supply alone. The memo flagged "no plant-capacity or balancing constraints" as a caveat; the real
model shows that caveat was load-bearing, not minor. **The Bronx figure must not be filed.**

What replaces it is stronger because it is in the record rather than modelled: four county
schedules were before USDA and it adopted the most racially graded (2.62¢ / 3.36¢ / 4.60¢ /
**5.05¢**), cutting the producer proposal in 2,153 counties and raising it in 419, with cuts
systematically smaller where the Black share was higher (t +12.08). See
`reports/counterfactual.md`.

---

## What was confirmed

- **§1 headline.** Reproduces to the cent on USDA's own county universe. Added: the $1.27/cwt
  level increase produced *none* of the widening — all +1.8¢ is re-sloping.
- **§3.** Strengthened. The metro-identical-differential point now has independent retail
  corroboration from the Atlanta null, which is the same fact seen from the other side.
- **§6.** Audited and confirmed — three-sentence certification, zero occurrences of consumer,
  retail, household, WIC, SNAP, incidence or low-income across 590,370 characters. Two findings
  added: the $4.01bn transfer with no consumer analysis, and the unanswered consumer-incidence
  comment. One precision added: the certification screens for impacts on *"FMMO participants"*,
  and USDA's narrow reading is long-standing, which is a defence rather than a vulnerability.
- **§6 detail corrected.** The memo said *"WIC appears only as Wichita."* The word-boundary
  count is zero; the substring hits are BRUNSWICK, SEDGWICK, WICHITA and WICOMICO. Substantively
  right, incomplete as stated — and it is quoted to a lawyer, so it was made exact.

## What was added

- *Block v. Community Nutrition Institute*, 467 U.S. 340 (1984) — review of milk marketing
  orders confined to handlers. The memo raised standing via WIC (§8) without the obstacle.
- A named discovery target: the **May and October 2021 USDSS runs** the schedule was actually
  built on, quoted in NMPF-38 but never filed as a county table.
- The PA/NJ statutory retail comparison ($4.75 vs $3.47) as context for why the withdrawn retail
  finding was implausible in the first place.

## Deliberately left alone

**§8, the California WIC analysis.** Not re-audited — it rests on a separate CDPH dataset this
project never held. The revision says so rather than implying it was checked.


---

## Addendum: §4a rewritten around the regional framing

Two problems with the first draft of §4a, both raised by the client and both real.

**It was unreadable.** It used "shadow prices", "state-block permutation", "give-up charge",
"leave-one-out runs" and bare *t*-statistics without glossing any of them, and it put the
significance column in the same table as the magnitudes — where the *p*-ordering (4.68¢
marked "no, p .074" beside 5.59¢ marked "yes, p .041") invites the reader to conclude the
freight gap is not real. Rewritten: every term defined where it appears, significance moved
into prose, and the table reduced to what each map is and what gap it carries.

**The national test was the wrong specification.** See `reports/above_cost_regional.md`. §4a
now leads with the regional decomposition — South +3.92¢/gal and Northeast +2.09¢ above the
freight model, West −6.58¢ below it, 73.9% of Black Americans in a marked-up region against
54.1% of white Americans — and states plainly that inside a region the markup does not track
race, that this is the right shape for a disparate-impact claim rather than a weakness, and
that a targeting theory is refuted by the same data.

The three limits are now a bulleted list rather than buried prose: the regional pattern's
racial incidence is still not significant (p .289); the within-region gradient is negative
and under region controls significantly so (t −2.36), which is the rebuttal to any filing
asserting otherwise; and above the freight model is not the same as unjustified, given USDA's
producer-revenue objectives.

Section 5's "establishes" and "does not establish" lists and the corrections table were
updated to match. The §4a entry in the corrections table no longer reads "adverse" — the
finding cuts both ways and the table now says so.


## Addendum 2: the docket record added to §6, with the citation

§6 previously compressed the unanswered-comment finding into one bullet. It is now set out in
full, because it is the strongest procedural fact in the memorandum and it is documentary.

- **128 comments and exceptions** (docket AMS-DA-23-0031, due 13 September 2024), after 49
  hearing days. 39 from dairy industry organisations; 89 from individuals, individual dairies
  and CME Group; **0 from consumer, anti-hunger, nutrition, faith, community or civil-rights
  organisations.**
- Keyword incidence across all 128: consumer 55, civil rights 16, affordability 10,
  **WIC 1, SNAP 1** — and both the WIC and SNAP hits are the *same filing*.
- That filing is cited in the document: **Milk Innovation Group, *Comments, Exceptions, and
  Objections to USDA's Proposed Rule*, AMS-DA-23-0031-0080, posted 16 September 2024, 55 pages,
  filed through Davis Wright Tremaine LLP.** Its numbered objections 2, 3 and 4 are quoted
  verbatim.
- Against the final rule's **zero** occurrences of "consumer" (`cria_audit.md`), that is a
  fully formed APA failure-to-respond predicate, and it requires proving no disparity at all.
- A note flags that MIG is a processor group — a *handler* — so under *Block* the one filer who
  put consumer incidence on the record is also among the few parties who could litigate it.

One sentence in the earlier draft was garbled — "requires proving no disparity at all" where it
should read "does not require proving any disparity at all." Fixed.

**Also added to §4a.** The same MIG filing objects that USDA "deviat[ed] from the USDSS model"
and used "current Class I differentials as a floor," which "artificially enhances fluid milk
prices." That is a contemporaneous, represented-party allegation of precisely what §4a measures,
which USDA did not answer — contemporaneous corroboration rather than a retrospective
reconstruction.
