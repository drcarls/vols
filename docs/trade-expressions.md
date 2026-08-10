# Trade Expressions — companion to the Instrument Problem desk note

*Concrete structures for each situation on the live map: the thesis, the primary expression, a
relative-value or alternative, the carry/sizing note, and what kills it. These are **illustrative of
how the framework maps to expressions** — not investment advice, not a solicitation. Almost all are
right on **instrument** and hard on **timing**; several are crowded and negative-carry. Size as risk
discipline dictates.*

---

## How to structure anything on this list (the meta-rules)

- **Buy the *exposed-instrument* vol, not the index vol** — oil vol for Iran, semis skew for Taiwan.
  It's usually cheaper and cleaner than SPX, and it's the thing that actually moves.
- **Prefer defined-risk convex structures** (spreads, not naked shorts/longs) — given negative carry
  and timing uncertainty, you want bounded bleed and bounded loss.
- **Trade the resolution:** own optionality *into* cheap vol / calm, and **monetize or roll on the
  spike** — don't hold to expiry hoping the forecast comes true.
- **Prefer the relative-value version** where a naive proxy *and* a real instrument both exist — the
  *divergence* is often the cleanest, best-carry trade.
- **Size by role:** tail hedges as *insurance* (bps of NAV, expect bleed); structural themes as
  *allocations* (scale in, don't chase); RV as *risk-budgeted* pairs.

---

## The expressions

### 1. China / Taiwan — the un-priceable tail (insurance, not harvest)
- **Thesis:** calm index ≠ low risk; the exposure is chips and the yuan, and the full-war tail can't be
  priced — so buy cheap convexity where it's exposed.
- **Primary:** 6–18m OTM **put spreads on SOX or TSM** (buy ~15–25% OTM, sell a further-OTM put to
  cheapen). **USDCNH topside call spreads** — CNH is the pressure valve, and FX convexity is often
  cheaper than equity puts. Long **TWD vol / USDTWD calls**.
- **RV:** long **semis skew vs SPX skew** (semis tail is cheap relative to its systemic importance); or
  SOX puts financed by SPX puts — own the *exposed* tail against the *index*.
- **Carry/size:** bleeds for years; size as insurance and roll.
- **Kills it:** in a *real* war, exchange/settlement/broker risk means the hedge may not pay — so pair
  with real-economy **supply-chain diversification** (avoidance, not just options). China policy support
  can also cap CNH.

### 2. Dollar-weaponization / de-dollarization — structural gold
- **Thesis:** the signal is central-bank gold demand and the flows (TIC, CIPS), not DXY; gold rising
  *with* real rates is the tell.
- **Primary:** a **strategic gold allocation** (physical/ETF) as exposure to the price-insensitive
  central-bank bid; **miners (GDX)** for beta.
- **RV:** long **gold vs long-end real rates** (the divergence *is* the thesis) — a cleaner risk profile
  than outright gold.
- **Carry/size:** allocation, not momentum; extended and consensus, so scale in on dips, watch
  positioning.
- **Kills it:** a real-rate spike, a dollar-funding squeeze, a positioning washout.

### 3. Norway / NOK — separate the two views
- **Thesis:** NOK is a risk/liquidity proxy first, energy a distant second; don't express energy through
  the currency.
- **Primary (energy view):** long **Equinor / European nat-gas (TTF) / energy equities** — *not* NOK.
- **NOK view (if any):** treat it as a **risk-off / carry** expression, not energy.
- **RV:** long **Equinor vs short NOK** — own the energy, neutralize the currency's non-energy drift
  (know both legs: this isolates the petro-earnings from the risk-proxy beta).
- **Kills it:** conflating the two — trading NOK expecting an energy beta.

### 4. Russia / Ukraine — the exposed instruments, never the ruble
- **Thesis:** the war's economic signal lives in gas, grain, and the Urals discount; the ruble is a
  managed propaganda price.
- **Primary:** long **TTF (European gas) call spreads** for supply-disruption/escalation; long **wheat
  calls** (Black Sea).
- **Adjacent:** the **Urals–Brent discount** via **tanker rates (VLCC/Aframax) and shipping equities**
  — the sanctions-evasion gauge; **European industrials/utilities** as the gas-exposed real economy,
  hedged with TTF.
- **Avoid:** the **ruble** — capital controls, convertibility and settlement risk; not a signal, not a
  trade.
- **Carry/size:** TTF and wheat mean-revert hard → defined-risk spreads, monetize spikes.
- **Kills it:** mean reversion, a ceasefire, negative carry.

### 5. Iran / Hormuz — the tradeable tail (resolution trade)
- **Thesis:** the Hormuz premium is real only while the strait is actually shut; the market is poor at
  forecasting the closure and fast at pricing it.
- **Primary:** own **Brent call spreads** (~3–6m, 10–25% OTM) as Hormuz insurance **when the strait is
  open and oil vol is cheap**; monetize/roll when a scare spikes vol.
- **Fade the scare:** after a spike likely to be a *scare* (telegraphed/symbolic response), **sell rich
  upside/vol — as a spread, never naked** against a real closure.
- **RV / decompose:** compare **Hormuz prediction-market P(closure) to the oil-implied premium (size)**
  and trade the gap; **VLCC rates** as confirmation.
- **Carry/size:** theta bleed through calm → spreads, roll; the resolution is the payoff.
- **Kills it:** bleed through calm; a real, executed closure if you're short.

### 6. US fiscal — the long end, not equities
- **Thesis:** debt-sustainability risk shows in the term premium and gold, never in an equity index at
  highs.
- **Primary:** **5s30s steepeners**; **long-end payer swaptions / TLT puts** for the fiscal tail; **gold**
  as the no-anchor hedge.
- **RV:** 30y **real yields vs gold**; **nominal 30y vs breakevens** (term premium or inflation?).
- **Carry/size:** negative carry, slow, whipsaw-prone (the long end rallies in risk-off) → convex,
  patient, small, defined-risk.
- **Kills it:** a risk-off long-end rally; fiscal consolidation; carry. (This trade has gored many —
  respect it.)

### 7. AI / concentration — trade the concentration, not the level
- **Thesis:** the index level hides that a handful of names carry the risk.
- **Primary:** **equal-weight vs cap-weight (RSP/SPY)** for breadth; **dispersion** (long single-name
  vol / short index vol) to monetize concentration.
- **Adjacent:** **semis** are the exposed instrument for both the AI upside and the Taiwan tail
  (asymmetric); watch the **private-credit / HY funding** of the datacenter-and-power capex — short it
  if the funding cracks.
- **Carry/size:** breadth and dispersion bleed in a melt-up → risk-budgeted RV, not outright short.
- **Kills it:** a momentum melt-up; dispersion staying pinned low.

### 8. Private credit / CRE / regional banks — where the marks don't move
- **Thesis:** stress hides in illiquid private marks; the public price is silent until a forced mark.
- **Primary:** **KRE puts** (regional banks); **CMBX** shorts on the riskier tranches (CRE); **BDC**
  equity/credit shorts for private-credit mark risk.
- **Carry/size:** negative carry until a catalyst (a forced mark / redemption wave); size for patience;
  mind basis risk in the proxies.
- **Kills it:** extend-and-pretend continues; rate cuts relieve CRE; no forced mark arrives.

### 9. Japan / JGBs — the spillover more than the bond
- **Thesis:** BOJ-normalization risk shows in the JGB long end and, more importantly, in what a
  carry-unwind does globally — not in USDJPY spot.
- **Primary:** short **JGBs / long JGB payer swaptions**; **long yen vol** (or long yen) to hedge the
  global carry-unwind spillover.
- **Carry/size:** the widowmaker — negative carry, the BOJ can pin it; small, convex.
- **Kills it:** BOJ yield control persists; carry.

---

## The one-paragraph summary for the desk

Own convexity in the **exposed** instrument, not the index: **Brent** for Iran, **SOX/CNH** for Taiwan,
**TTF/wheat** for Russia, the **long end/gold** for US fiscal, **breadth/dispersion** for AI, **KRE/CMBX**
for credit, **JGB payers** for Japan — and **gold** as the structural read on the sanctions-weapon decay.
Express energy as **gas and equities**, never the **krone** or the **ruble**. Trade the **resolution**,
not the forecast; prefer **defined-risk spreads** and **relative-value divergences**; treat the
**un-priceable** tails as insurance you expect to bleed on. The framework's edge is knowing *which
instrument* — the timing and the sizing are still yours, and the honest part is that most of these are
right on instrument and hard on when.

*Companion to `instrument-problem-desk-note.md` and `pricing-geopolitical-risk-READER.md`. Framework and
risk disciplines only; not investment advice; illustrative structures; 2026 levels move.*
