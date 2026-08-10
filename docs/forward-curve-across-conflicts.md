# Reading the forward curve — oil, and every other conflict

*The Ukraine lesson generalizes: for any conflict, the market's **forward expectation** — how long it
thinks the disruption lasts and where it settles — lives in the **term structure of the exposed
instrument**, not the spot price. But the *shape* that term structure takes changes with the
instrument. This note does oil/Iran (the direct analog), then the general law, then the one unifying
pattern that ties it to the discrimination ladder.*

---

## Oil / Iran — the direct analog to Ukraine gas

Brent's forward curve carries the same forward information the TTF curve did for Ukraine. Crude is
normally in **backwardation** (front above deferred). When Hormuz is threatened:

- the **front spikes and backwardation steepens** — the market pricing *acute near-term* supply risk it
  expects to *ease* (the classic "temporary" signal);
- the **prompt-vs-deferred spread** is the tradeable read of **"how long does the market think the
  strait stays contested?"** — a wide front premium says *weeks*, a lift in the whole curve says
  *structural*;
- **June 2025** (scare, strait open): the front jumped and *fell back below* start within days — the
  curve said "temporary," and it was; **spring 2026** (strait actually shut): the front ran to $114 and
  **held above $100 for two months** — the curve stayed elevated further out, pricing a *real,
  persistent* disruption. Same instrument, and the *duration* of the backwardation discriminated scare
  from closure.

So the oil read is identical in structure to the wheat/gas read: **backwardation depth = how
temporary; the out-months = where it settles; the calendar spread = the timing of resolution; options
skew = the escalation tail.** (Spot arc, Brent: ~$75 pre-war → ~$108 2022 → ~$83 Aug 2026 — reproducible
`BZ=F`; the live signal is in the contract-month spreads.)

## The general law — every instrument has its term structure

The Ukraine/oil insight is a special case of a universal one:

> **The spot price says the crisis is here. The term structure of the exposed instrument says what the
> market expects next — its duration and its resolution.**

What plays the role of "the curve" depends on which instrument carries the risk:

| Conflict type | Exposed instrument | Its "term structure" | An *inversion* means |
|---|---|---|---|
| **Commodity** (Iran oil, Ukraine gas/wheat, Red Sea) | oil, gas, wheat, freight | **futures backwardation / calendar spreads**; FFAs for freight | acute-now, expected to *ease* |
| **Sovereign / credit** (Russia, Venezuela, Argentina, a default) | CDS, sovereign bonds | **CDS term structure & the bond curve** — short-dated CDS *above* long | a near-term event (default/survival) the market expects to *resolve soon* |
| **Currency** (Brexit, EM pegs, the ruble) | FX | **forward points / NDFs & risk-reversal skew** | expected *devaluation* (and the NDF reveals what a *managed* spot hides) |
| **Equity / systemic** (Taiwan, general-war scares) | index / sector vol | **VIX term structure & options skew** — spot vol *above* forward vol | acute fear expected to *pass* |
| **Rates / fiscal** (US debt ceiling) | Treasury bills | **the bill maturity ladder** — a *kink* at the X-date | the market dating *where* the risk concentrates |
| **The decision itself** (any) | prediction markets | **the maturity ladder of odds** (P by Dec vs by Jun) | the crowd's *timing* of the political decision |

The move is always the same: **don't read the spot — read the shape.** An inverted/backwardated
structure is the market saying *"severe now, survivable, temporary."* A flattening or a lifting of the
back end is it saying *"this is becoming structural."*

## The one unifying pattern (and the tie to the ladder)

Across all of them, the term structure behaves the same way by rung:

- **Localized / survivable disruption → the curve *inverts* (backwardation, inverted CDS, inverted
  VIX):** the market prices an acute-but-temporary event and tells you, in the shape, *when* it expects
  resolution. This is where the forward information is richest and most tradeable (Ukraine gas, Iran
  oil, a sovereign in an event).
- **Existential / un-priceable → the curve goes *silent*:** for a true Taiwan-style war, the VIX term
  structure does *not* invert dramatically and the far-dated tail stays cheap — **because you cannot
  price a catastrophe you will not survive to collect on.** The *absence* of a term-structure signal is
  itself the tell that you've hit the ceiling. A flat curve into a genuine existential risk is not calm
  — it's un-priceability.

So the term structure is the same tool everywhere, and it even diagnoses its own limit: **it carries
forward information precisely where the risk is survivable, and it falls silent exactly where it
isn't.**

## The discipline (unchanged)

The curve prices the **exposed channel's** expected resolution — supply for commodities, default-timing
for credit, devaluation for FX — **not the underlying military/political decision.** It is the
anticipation channel operating on the *handicappable sub-question* ("how long is Black Sea grain
blocked," "how long is Hormuz contested," "does this sovereign survive the next coupon"), which it does
well, and it is *not* a forecast of "will they escalate," which it does badly. Read it as *expected
disruption duration*, a proxy for the conflict's intensity — never as a war oracle. And where you want
the decision itself, that's what the **prediction-market maturity ladder** is now for — the one term
structure that prices the political choice directly (thin and manipulable, so a lead, not a truth).

*Worked example with data and chart: `ukraine-futures-forward-info.md` (TTF gas 12× then normalized;
the 2022 backwardation's "temporary" call, realized). Framework/risk only; not advice; the
term-structure signal sits in the individual contract months (ICE/CME), beyond the spot series here.*
