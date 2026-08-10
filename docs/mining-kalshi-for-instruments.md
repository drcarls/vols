# Mining Kalshi for more things to price

*Kalshi is a giant map of **decision-probabilities**. The instrument-problem framework turns each one
into a tuple — `Kalshi P(event)` → **exposed instrument** → **tradeable names** — so "what Kalshi
prices" becomes a discovery engine for *more things to price*. The work is the **filter**: most Kalshi
markets are not tradeable this way, and the framework tells you which to keep.*

---

## What Kalshi actually prices (1,200 events, live)

Enumerating the Kalshi event universe (`kalshi.list_events()`), 14 categories:

| Category | ~count | Framework-tradeable? |
|---|---:|---|
| Elections | 664 | **Mostly no** — instrument-less (NATO SG, next Pope). A few map (a G7 leader change → that country's assets). |
| Politics | 178 | **Some** — legislation → policy instruments (tariffs, drug pricing, energy). |
| Entertainment | 88 | **No** — next Bond, next Rambo. No instrument. |
| Sports | 84 | **No.** |
| **Economics** | 64 | **Yes** — Fed funds, CPI, GDP → rates, bonds, banks, cyclicals, gold. |
| **Financials** | 44 | **Partly** — IPO races → the fintech/underwriter complex, comparable publics. |
| **Companies** | 34 | **Yes (single-name)** — antitrust (LYV), CEO succession (JPM), AGI timing → semis. |
| Science & Tech | 21 | **Rarely** — fusion → nuclear/uranium; most (Mars-by-2050) are **un-priceable**. |
| **Climate & Weather** | 11 | **Partly** — hurricanes/quakes → insurers, energy, ag; but 2°C-by-2050 / supervolcano are **un-priceable**. |
| **Health** | 4 | **Yes (single-name)** — FDA approvals → the specific biotech. |
| World / Social | 6 | **Some** — Trump–Putin meetings, EU expansion → geopolitical. |
| Crypto | 1 | **Yes** — BTC/ETH ranges, ETF → COIN, MSTR, miners. |

## The filter — three tests to keep a Kalshi market

Not every priced probability is a tradeable mispricing. Keep a market only if it passes all three:

1. **Real exposed instrument.** Does `P(event)` map to an instrument whose price moves on the event —
   oil, rates, a biotech, an insurer, a currency? If not (Sports, Entertainment, the Pope), discard.
2. **Tradeable horizon.** Does it resolve on a horizon you can hold and collect on? A "by 2050" market
   is not a trade; a Fed decision, an FDA date, a hurricane season, a Hormuz-by-year-end is.
3. **Not un-priceable.** Drop the civilizational tails — 2°C-by-2050, a supervolcano, "colonize Mars."
   The market cannot price a catastrophe it won't survive to collect on; its Kalshi odds are opinion,
   not a hedge, and the exposed instrument stays silent (the Cuba ceiling, generalized).

What survives is a **broad, multi-category event universe**, far beyond the six geopolitical events the
sleeve started with.

## The instrument map (what survives, by category)

| Kalshi category | Event | Exposed instrument → names (signed) |
|---|---|---|
| **Macro** | Fed hike / higher-for-longer | banks **+** (KRE, JPM), long duration/growth **−** (TLT, ARKK), gold **−** |
| | Fed cut | long duration **+** (TLT), growth **+**, gold **+**, banks **−** |
| | CPI hot | energy/materials **+** (XLE, FCX), gold **+**, long bonds **−** |
| | Recession | defensives **+** (XLP, XLU), cyclicals/HY **−** (XLY, XLI, HYG) |
| **Policy** | New tariffs | import-substitutes **+** (X, NUE), importers/targets **−** (GM, NKE, FXI, EWW) |
| | Drug-pricing reform | pharma/PBMs **−** (PFE, MRK, LLY, CVS, UNH) |
| **Company** | Antitrust ruling | the named single-name **−** (e.g. LYV) |
| | AGI milestone | semis / AI complex **+** |
| **Health** | FDA approval | the specific biotech **+**, competitors **−** |
| **Climate** | Major hurricane | insurers/reinsurers **−/+** (ALL, TRV; RNR pricing-power **+**), gulf energy/refiners **+** |
| **Crypto** | BTC/ETH rally / ETF | crypto-exposed equities **+** (COIN, MSTR, MARA) |
| **Geopolitics** | Hormuz / Red Sea / Taiwan / rare earths / rearm | oil, freight, semis (−, un-priceable), miners, defense |

These are wired into `DEFAULT_EXPOSURE_MAP` (`data/geopolitical.py`) — geopolitics is now just one
block. The sleeve is, in truth, a **prediction-market mispricing engine**; geopolitics was the first
category, not the boundary.

## The discovery workflow

```python
from pari_mutuel_trader.data.kalshi import list_events
# 1. enumerate what Kalshi prices, by category
for e in list_events(category="Economics"):
    print(e["event_ticker"], "-", e["title"])
# 2. keep the ones with a real instrument + tradeable horizon (drop un-priceable/long-dated)
# 3. add {event, kalshi_ticker, premium} to configs/geopolitical.yaml and a row to DEFAULT_EXPOSURE_MAP
# 4. build-features -> the sleeve prices the odds-vs-premium gap across the whole universe
```

Each kept market becomes the same trade the sleeve already runs: **`edge = P(Kalshi) − premium(instrument)`**,
tilt toward beneficiaries and away from victims when the odds diverge from what the instrument prices.

## Why this matters

The single instrument (oil, semis, freight) was never the point — it was the *first* instrument. Kalshi
prices the anticipation channel across **macro, policy, single-name, health, climate, and crypto**, and
the framework maps each survivor to its exposed instrument. So "more things to price" is literal: the
mispricing detector — *decision-odds vs the premium already in the instrument* — runs on **dozens** of
Kalshi markets, not six. The discipline is unchanged and doubly important at scale: keep only the
markets with a real instrument and a survivable, near-dated resolution; the rest is noise the crowd is
happy to bet on and the market cannot hedge.

*Companion: `pari_mutuel_geopolitical_sleeve.md`, `mispricing-worked-example.md`,
`forward-curve-across-conflicts.md`. Framework/risk only; not investment advice; exposure maps are
illustrative defaults — verify tickers and signs for a live book.*
