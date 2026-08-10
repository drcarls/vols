# A mispricing, and how to trade it — worked example

*"Mispricing" here has a precise meaning: not "the market is dumb," but **the decision-odds (from
prediction markets) diverge from the disruption premium the exposed instrument is actually pricing.**
The framework gives you a repeatable detector — decompose, compare, trade the gap. Illustrative of the
method; live inputs (Kalshi P, oil implied-vol/skew, the freight curve) come from a data feed — this
book's stock-picker already carries the Kalshi side.*

---

## The detector (the recipe)

1. Find the **exposed instrument** (oil for Iran, freight for the Red Sea, semis for Taiwan — never the
   index).
2. Read its **implied premium** — implied vol / skew / term-structure backwardation — i.e. the
   probability-weighted disruption the *instrument* is pricing.
3. Read the **decision-odds** for the same event off the **prediction market** (Kalshi/Polymarket P).
4. The **mispricing is the gap**: `P(prediction market)` vs `P implied by the instrument`.
   - **Odds rich, premium cheap** → the instrument is *under-pricing* the tail → **buy convexity**.
   - **Premium rich, odds cheap** → the instrument is *over-pricing* it (a fading scare) → **sell/fade**.
5. Trade the gap with **defined-risk convexity in the exposed instrument**; size as insurance; the kill
   is the gap closing against you.

The key move: `oil premium ≈ P(disruption) × size`. Read **P** off Kalshi, **size** off the oil curve —
and if the two Ps disagree, one of them is the trade.

## The worked example — Hormuz, and why it's two-sided *right now*

**The instrument read (live).** Oil implied vol (OVX) is **~55** as of early August 2026 — *elevated*,
off a mid-July spike to ~64, against a calm-regime ~27–30 and a spring-2026 crisis peak of ~108. So oil
is **already pricing meaningful Hormuz/Red Sea risk** — it is *not* complacent today.

That changes which side of the trade is live:

- **If Kalshi's P(Hormuz closure/incident by year-end) is *below* what OVX ~55 implies** → oil vol is
  **rich**, the market is over-paying for a tail the odds don't support → **fade it**: sell the rich
  front vol / upside as a *spread* (never naked), or sell a call-spread against a real-closure cap. This
  is the *scare-premium harvest* from the "trading the quiet" playbook — and with OVX elevated, this is
  the more likely live side.
- **If Kalshi's P sits *above* the OVX-implied premium** → oil is under-pricing the tail → **own Brent
  call spreads / a call calendar** (buy the cheap deferred, sell the collapsed front).

**Why the calm version is the cleaner recurring trade.** The framework predicts a *systematic* version
of the "buy" side: **when a scare resolves and OVX mean-reverts to ~30, oil forgets the standing risk
(it's a resolution-pricer), while Kalshi keeps a standing decision-probability.** That is the
recurring mispricing — *cheap tail in the calm* — and the disciplined rule is: **fire the buy when OVX
is back near its calm floor and Kalshi P is still non-trivial; fire the fade when OVX is elevated and P
is lower than the premium implies.** Today (OVX ~55) the window for the buy is *closed*; the fade is
the candidate — pending the actual Kalshi print from the feed.

**The trade, either way:** defined-risk (spreads, calendars), insurance-sized, and it pays/loses on the
*resolution* — a real Hormuz incident closes the gap violently in the buyer's favour (front vol and
backwardation re-spike, as in spring 2026); a durable ceasefire closes it in the fader's favour.

## A second, different *type* — a duration mispricing (Red Sea freight)

Different curve, different failure mode. Shipping **forward freight (FFAs)** may price a **quick Red Sea
reopening** (near-term rates high, forwards sloping to normal) while the framework's read *and* the
shipping consensus (Houthis persistent, Cape routing the default **through 2027**) say the disruption is
**structural**. If the curve prices *temporary* where the reality is *persistent*, **deferred freight is
too cheap** → own deferred FFAs / the shipping equities the curve is pricing to normalize but won't.
Mirror image if a reopening is nearer than the curve thinks. The gap here is **duration**, not
probability — same recipe, different instrument.

## From trade to *sleeve* — the systematic version

The same detector becomes a stock-selection tilt, which is why it belongs as a sleeve in the equity
book (see `pari_mutuel_geopolitical_sleeve.md`). For each live event with a Kalshi probability:

> **signal(stock) = P(event | Kalshi) × exposure(stock → the event's instrument) − premium already in
> that instrument (OVX / skew / curve)**

Go **long** the exposed equities when the odds are rich and the instrument premium is cheap (the market
hasn't put the decision-odds into the names yet); **stand down / trim** when the premium already
reflects the odds. Examples of the exposure map: Iran/Hormuz → energy & tanker names; Red Sea → shipping
& freight; Taiwan → semis (insurance only — un-priceable); rare earths → miners/processors; rearmament →
defense primes; Venezuela → oil & specific E&P/credit. The sleeve is long-only and tilts the existing
universe; it does not try to time the war — it tilts toward names carrying a **decision-odds-vs-premium
gap** the rest of the book isn't pricing.

## The honest caveats

- **This is the detector, not a live call** — the exact gap needs the live Kalshi P and the oil
  vol/skew/freight curve; OVX ~55 today says the *buy-the-calm* side isn't open, which is itself the
  discipline (don't buy a tail that's already priced).
- **Right on instrument, hard on timing** — defined-risk, convex, patient; the edge is the *detection*
  (the framework tells you where the gap can be), not the when.
- **Prediction-market P is thin and manipulable** — a lead, not a truth; verify the print before
  trusting the gap.

*Companion to `trade-expressions.md`, `forward-curve-across-conflicts.md`, and the geopolitical sleeve.
Framework and risk only; not investment advice.*
