# Ukraine — what wheat and energy futures actually tell you about the war

*Short answer: yes, there is forward information — but it lives in the **term structure** (the shape of
the forward curve and the calendar spreads), not the spot price. The curve encodes the market's
expected **duration and resolution** of the supply disruption, and in 2022 it beat the narrative.
The discipline: it prices the **supply channel's** expected normalization — a proxy for the conflict's
expected intensity — not the military/political decision itself.*

---

## The exposed instruments, and the spot arc

Ukraine's war prices through **wheat** (Russia + Ukraine ≈ a third of world wheat exports; Black Sea
ports blockaded) and **European gas / TTF** (Russian pipeline flows cut). The spot record:

- **Wheat (Chicago, ¢/bu):** 671 (Jun '21) → **1006 on the invasion (+50%)** → 809 (Aug '22) → 665
  (Jul '23) → 559 (Jan '25) → **538 (Jan '26)** → 640 (Aug '26). Spiked, then **normalized below the
  pre-war level** as global supply adjusted and Ukraine re-routed via the Danube and land.
- **TTF gas (€/MWh):** 35 (Jun '21) → 126 (Mar '22) → **240 (Aug '22, ~7× — intramonth higher)** → 28
  (Jul '23) → 53 (Jan '25) → 39 (Jan '26) → 55 (Aug '26). Spiked to a generational extreme, then
  **collapsed back to ~€30** as Europe re-balanced (LNG, demand destruction, storage) — settling at a
  structurally-higher "new normal" (~€30–55) than the pre-war €20.

Chart: `war_premia/results/ukraine_wheat_gas.svg`.

## Where the forward information actually is — the term structure

Spot tells you the crisis is *here*. The **curve** tells you what the market expects *next*:

- **Depth of backwardation (front months above deferred) = how *temporary* the market thinks it is.**
  At the 2022 peaks, both wheat and TTF were **steeply backwardated** — the front bid far above the
  out-years. That is the market saying, in price, *"acute now, but we expect it to ease."* **It was
  right** — the deferred contracts were pricing the normalization that arrived in 2023–24, while
  commentators were forecasting a permanent energy crisis.
- **The out-year forward level = where the market thinks it *settles*.** TTF forwards for 2024–25 sat
  far below the €240 front — encoding "Europe solves this, but at a higher floor than pre-war." Also
  realized (~€30–55).
- **Calendar spreads = the market's *timing* of resolution.** The front-vs-deferred spread is the
  tradeable "when does the disruption clear?" And for gas specifically, the **winter-vs-summer spread**
  is the *war-risk premium priced into the heating season* — the cleanest single read of expected
  war-related tightness.
- **Options skew / implied vol = the *escalation tail*** — how much the market pays for a further
  supply shock.

## It updates on the war's events (the resolution channel, live)

The curve reprices cleanly on each **supply-relevant** decision — which is exactly the "trade the
resolution" pattern:
- **Black Sea Grain Initiative (Jul 2022)** → wheat backwardation collapsed (exports resumed).
- **Russia exits the deal (Jul 2023)** → re-steepened, but *less* — the market had learned the
  alternative routes worked (adaptation priced in).
- **Nord Stream cut / sabotage, pipeline and port attacks** → TTF front spikes, winter spread widens.

So you can read the market's evolving expectation of the war's *supply impact* off the curve in real
time.

## The discipline — what it does and does not forecast

This is the framework's anticipation/resolution line, applied:
- The curve is **good** at the *supply-logistics* question — "how long will Black Sea grain be
  disrupted," "can Europe replace Russian gas" — because that is a handicappable, physical problem.
  There it carried genuine forward information and **beat the narrative**.
- It is **not** a forecast of the *military/political* decision — "will Russia escalate, will there be
  a ceasefire." Those are the un-handicappable decisions the anticipation channel is weak on.
- So the forward info is a **proxy for expected disruption duration/intensity**, not a war oracle.
  Read it as "the market expects the *supply* effect to last X and settle at Y," not "the market thinks
  the war ends in Q3."

## What the curves say *today* (Aug 2026)

Both have **ticked up** off their early-2026 lows — wheat ~640 (Kansas ~714), TTF ~€55 (from €39 in
January). The framework's instruction: **don't read the spot tick — read the spread.**
- If the move is **front-loaded backwardation**, it's a *near-term* supply issue (weather — the Kansas
  premium hints at US drought) that the curve expects to pass.
- If the **whole curve lifts** (out-years up, winter spread widening), the market is pricing a
  *persistent* war-related tightening into the heating season.

That distinction — weather vs war — is exactly the forward information you can extract right now, and
it's in the calendar/winter spreads, not the headline price.

## The tradeable version

The calendar spread *is* the "when does the market think this resolves?" trade: own front-vs-deferred
to express a view on disruption duration; the **winter-vs-summer TTF spread** to trade the war-risk
premium in the heating season; options skew for the escalation tail. And watch them **update on the
grain-corridor and pipeline events** — that's where the resolution repricing lands.

*Data: Yahoo `TTF=F` (Dutch gas), `ZW=F` / `KE=F` (wheat), `BZ=F` (Brent), reproducible. Term-structure
/ calendar-spread detail requires the individual contract months (ICE/CME) — the spot series here shows
the arc; the forward curve is where the live signal sits. Framework/risk only; not advice.*
