# The geopolitical mispricing sleeve (pari_mutuel_trader)

*A new sleeve in the weekly long-only US-equities stock-picker. It turns prediction-market
decision-odds (Kalshi/Polymarket P) into a per-name equity tilt via the instrument-problem logic:
the risk of a conflict lives in a specific **exposed instrument**, and the edge is the gap between
the **decision-odds** and the **premium the instrument already prices**. It plugs in as an ordinary
`Agent`, so it is softmax-pooled, hedge-weighted, and separately attributed like every other book.*

---

## The signal

For each live event `e` with market probability `prob_e` (from the Kalshi feed) and an implied
premium `premium_e` already in its instrument (both in [0, 1]):

```
geo_signal[symbol] = Σ_e  (prob_e − premium_e) · exposure[e][symbol]
```

- **`exposure` is signed.** A name that *benefits* from the disruption (an oil major when Hormuz is
  threatened; a defense prime on rearmament; a rare-earth miner on a China squeeze) has a **positive**
  weight; a name that is *hurt* (a chip designer if Taiwan is threatened) has a **negative** weight.
- **`edge = prob − premium`** is the mispricing. **Positive edge** (odds richer than the premium) →
  tilt **toward beneficiaries, away from victims** (the market hasn't put the odds into the names yet).
  **Negative edge** (the premium is already rich — a fading scare) → the reverse (fade / stand down).
- With no events supplied, the sleeve is **neutral** (all-zero) — it degrades gracefully, exactly like
  the news/macro agents when their column is absent.

The default exposure map (`data/geopolitical.py: DEFAULT_EXPOSURE_MAP`) covers **Iran/Hormuz** (energy
& tankers up, airlines down), **Red Sea** (shipping up), **Taiwan** (semis down — un-priceable, trim
only), **rare earths** (Western miners up), **rearmament** (defense up), and **Venezuela** (oil/E&P).
Override it for a live book.

## How it plugs in (no engine changes)

Following the repo's conventions exactly:
- `agents/geopolitical.py` — `GeopoliticalAgent(name="geopolitical")` reads the `geo_signal` column
  (zero-fill if absent), like `NewsIntensityAgent`.
- `agents/__init__.py` — registered in `build_v1_agents()`; the engine softmax-pools it into the
  pari-mutuel book, gives it a hedge-learned weight (starts 1/N, then `hedge_update` rewards it on
  realized performance), and attributes it separately.
- `data/features.py` — `geo_signal` added to the feature whitelist (default 0.0).
- `data/geopolitical.py` — `build_geo_signal()`, `attach_geo_signal(features_df, events)`,
  `load_events(path)`.

## Feeding it live — Kalshi is wired into `build-features`

The sleeve is populated **automatically** each time you build features. `cli.py: build-features` reads
`data.geopolitical_path` (default `configs/geopolitical.yaml`), resolves each event's `prob` from
Kalshi, and attaches the `geo_signal` column — no manual step. It prints, e.g.
`geo sleeve: attached geo_signal for 5 events (prob source: ['kalshi_live', 'static'])`.

Two inputs per event:
1. **`prob`** — the decision-odds, resolved in priority order by `data/kalshi.py`:
   **live** (GET the Kalshi market named by the event's `kalshi_ticker`) → **local file**
   (`KALSHI_PROBS_PATH`, a `{ticker: prob}` CSV/JSON your pipeline writes) → **static** (the `prob` in
   the config). So it works with no keys/network (static) and upgrades to live odds when a feed exists.
2. **`premium`** — the disruption already priced in the exposed instrument, from its implied vol /
   skew / term structure — **OVX** for oil, the **FFA curve** for freight, **semis skew** for Taiwan.
   This is what makes it a *mispricing* signal, not a fear gauge. (Config-set today; wire to a live OVX
   feed the same way if you want it automatic.)

Config: copy `configs/geopolitical.example.yaml` → `configs/geopolitical.yaml`, give each event a
`kalshi_ticker` (omit it for structural themes like `REARM` to keep them static), and set env in
`.env` (`KALSHI_API_BASE`, `KALSHI_API_KEY`, `KALSHI_PROBS_PATH` — all optional). Then just
`build-features` as usual and the tilt is live.

## The discipline (built into the design)

- **Two-sided, and honest about the regime.** With **OVX ~55 (Aug 2026, elevated)**, the oil premium
  is high, so `IRAN_HORMUZ` edge is likely ~0 or negative right now — the sleeve *tilts nothing* (or
  fades), which is correct: don't chase a tail already in the price. The clean *buy* fires when OVX
  mean-reverts to its calm floor (~30) while Kalshi keeps a standing probability.
- **Un-priceable ≠ tradeable.** Taiwan carries *negative* exposure (trim chip names) only — you can't
  harvest a premium the market can't price; the sleeve treats it as light insurance, never a short.
- **Prediction-market P is thin and manipulable** — a lead, not a truth. It enters as one input among
  the pari-mutuel book's several agents, and its influence is *hedge-weighted down* automatically if it
  doesn't perform. That is the right home for a noisy-but-informative signal: co-equal, attributed, and
  self-correcting.

## Run

```bash
cd pari_mutuel_trader && export PYTHONPATH=src
python3 -m pytest tests/test_geopolitical.py -q     # 7 passing
# then feed events via configs/geopolitical.yaml and rebuild features before backtest/paper.
```

*Companion: `mispricing-worked-example.md` (the detector and the Hormuz worked example),
`forward-curve-across-conflicts.md`, `live-board-2026.md`. Framework/risk only; not investment advice.*
