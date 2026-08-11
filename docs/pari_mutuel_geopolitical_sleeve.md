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
only), **rare earths** (Western pure-plays up), **rearmament** (defense up), and **Venezuela** (oil/E&P).
Override it for a live book.

### Instrument notes — which proxy actually carries the trade

The exposure map is only as good as the instrument behind each name. Two cases sit on opposite sides of
the instrument problem:

- **Rare earths — no clean instrument exists.** There is *no liquid Western-listed rare-earth (NdPr)
  future*; the metal prices on Chinese/OTC venues. So the theme is **forced into equity proxies**:
  **MP** is the only scaled US pure-play (magnet-metal miner); **LYSCF** (Lynas) is the ex-China
  pure-play but trades US OTC; **REMX**, the obvious ETF, is **contaminated** — it holds Chinese
  producers and lithium and can move the *wrong way* in a squeeze, so it carries only a small weight.
  A prior version mislabeled **ALB** (lithium) and **UEC** (uranium) as rare earths; they now sit in
  their own `LITHIUM` / `URANIUM` themes so they don't distort the rare-earth signal.
- **Oil — many instruments, ranked by contamination.** The *premium* prices in crude futures and
  **OVX**; use **Brent** (the Hormuz-relevant waterborne barrel), not landlocked WTI. **USO** bleeds
  roll yield in contango — never a hold; **BNO** (Brent) is the cleaner ETF. For a long-only stock
  book the expression is integrated/E&P equity plus **tankers** (FRO/STNG/INSW/DHT), which often lead
  on closure/reroute *fear* even when barrels are ultimately rerouted and flat price gives the move back.

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
2. **`premium`** — the disruption already priced in the exposed instrument, now **auto-fetched from
   implied vol** (`data/premium.py`): **OVX** for oil events, **MOVE** for rate/macro events, **VIX**
   for equity/systemic events — normalized to [0,1] as the fraction of the instrument's crisis range
   currently implied. Events with no clean vol proxy (rare earths, rearm, FDA) keep the static config
   `premium`. This is what makes it a *mispricing* signal, not a fear gauge.

Config: copy `configs/geopolitical.example.yaml` → `configs/geopolitical.yaml`, give each event a
`kalshi_ticker` (omit it for structural themes like `REARM` to keep them static), and set env in
`.env` (`KALSHI_API_BASE`, `KALSHI_API_KEY`, `KALSHI_PROBS_PATH` — all optional). Then just
`build-features` as usual and the tilt is live.

## Live entry, not hindsight — the resolution trigger

The backtest ladder (`geo-sleeve-backtest-ladder.md`) validated the *exit* discipline given a correct
entry, but its entries were placed with hindsight. `data/resolution.py` supplies the entry **live**,
off real Kalshi odds, closing that gap:

- **Watching** (odds `< activate_at`, default 0.5): `resolution_decay = 0` → **the sleeve tilts
  nothing**. Merely *anticipating* a decision is the weak channel; the sleeve does not trade it.
- **Resolved** (odds cross `activate_at`): `resolution_decay = 1.0` → **full tilt at the catalyst**.
  Entry is the odds crossing, recorded with the date — the strong (resolution) channel.
- **Settling**: `resolution_decay = 0.5**(weeks_since_activation / half_life)` → the tilt fades and
  the weekly rebalance **rotates the book out** — the validated exit, now running live.
- **Reversed** (odds fall back below `deactivate_at`): cleared back to watching (flat).

It sets a per-event `resolution_decay` that multiplies the `edge` in `build_geo_signal` (default 1.0
when unused, so nothing changes for callers that don't opt in), and persists *when* each event first
resolved to `data.resolution_state_path` so the decay clock survives across runs. Structural themes
with no `kalshi_ticker` (e.g. `REARM`) have no odds to resolve on and are left untouched.
`build-features` runs it automatically when the config path is set and prints, e.g.,
`resolution trigger: IRAN_HORMUZ=watching, RED_SEA=active`.

The honest limit: we can't fully *backtest* this trigger yet, because Kalshi odds history for these
bespoke events is sparse. But the mechanism is exactly the validated discipline (gate on resolution,
exit on a weeks-scale clock), now driven by live odds rather than hindsight — and the fix for the
backtest gap is accumulation, not more hindsight. `data/odds_log.py` + `scripts/log_odds.py` append a
dated `(prob, premium, resolution_state)` row per event on every run (idempotent per day) to
`data.odds_log_path`. Schedule `log_odds.py` weekly and, in a few months, you hold the genuine dated
panel a real trigger backtest needs — the entry side finally gets its own honest track record.

## Tying it to the existing sleeves — the Kalshi→macro_regime bridge

The sleeve is not a bolt-on; `edge = prob − premium` **is** the pari-mutuel objective the whole engine
runs on (true odds − pool-implied odds), just read across two venues (Kalshi vs the vol market). To
make that tie explicit, the macro events feed the repo's existing **`MacroRegimeAgent`** directly:

- `data/geopolitical.py: build_macro_regime(events)` projects the FED/CPI/RECESSION edges onto one
  risk-on/off axis — `regime = clip(Σ (prob − premium)·sign, −1, 1)`, with `FED_CUT +1`, `FED_HIKE /
  CPI_HOT / RECESSION −1`. A **cheap premium** (calm MOVE/VIX today) with standing odds → a
  large-magnitude regime; an **already-rich premium** → near zero — the same discipline as the name tilt.
- `attach_macro_regime(features_df, events)` adds that scalar into the `macro_regime` column
  (additive + clipped, so it composes with any returns-derived regime). `MacroRegimeAgent` then turns
  it into a per-name tilt via its existing `regime · (ret_20d − vol_20d)` — **prediction-market odds
  now set the regime sign** instead of (or on top of) realized returns.
- `build-features` wires it automatically and prints, e.g., `geo->macro bridge: macro_regime -0.42
  from Kalshi macro odds`.

So one Kalshi read now drives **two** sleeves — the geo name-tilt *and* the macro regime — expressing
the same view through two lenses. Any redundancy is handled by the hedge learner, which sizes each
sleeve on realized P&L. (Companion options not yet wired: an `edge = signal − priced` house primitive
retrofit to momentum/news, and geo-sign gating of momentum entries — "trade the resolution.")

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

## What the recommendations actually look like

The sleeve's output is a **per-name tilt** (`geo_signal`), not a buy list — the engine pools it with
the other agents and the hedge weight decides how much it moves the book. But read on its own, with
the example config (Aug 2026 odds; premiums auto-fetched), the tilts come out like this:

| Event | edge = prob − premium | Names it tilts (weight = edge × exposure) |
|---|---|---|
| **REARM** (structural, static premium) | 0.70 − 0.40 = **+0.30** | **LMT / RTX / NOC +0.30**, GD / LHX +0.24, HII +0.18 |
| **RED_SEA** | 0.55 − 0.35 = **+0.20** | **ZIM +0.24**, MATX +0.20, XOM +0.08, CVX +0.06 |
| **RARE_EARTH** (static premium) | 0.40 − 0.20 = **+0.20** | **MP +0.30**, ALB +0.12, UEC +0.12 |
| **TAIWAN** (un-priceable → trim only) | 0.08 − 0.03 = **+0.05** | **TSM −0.06**, NVDA / AMD −0.05, AVGO / ASML / MU −0.04, QCOM −0.03 |
| **IRAN_HORMUZ** (OVX elevated) | ~0.30 − ~0.30 ≈ **0** | **no tilt** — the tail is already in the oil price; the sleeve stands down |

Read plainly: **long the beneficiaries with a standing odds-vs-premium gap** (defense primes on
rearmament, box-shippers on the Red Sea reroute, the one Western rare-earth name), **lightly trim the
un-priceable victim** (chip names on Taiwan — insurance, never a short), and **do nothing on Hormuz**
because the premium already equals the odds. The single most important line is the last one: the
sleeve's job is as much *where not to tilt* as where to.

These are magnitudes on the sleeve's own scale; the book-level position is this tilt × the sleeve's
hedge weight, softmax-pooled with every other agent — so no single name is ever a large gross bet.

## What a historical return would look like

There are two honest ways to answer "what would this have returned," and they answer different
questions:

1. **A strategy backtest** — the engine metric — needs a *dated weekly (prob, premium) panel per
   event* to replay. We don't have that: Kalshi's markets for these bespoke events are recent and
   sparse, so a true Sharpe would be fit on a handful of weeks and would overstate. On the synthetic
   test universe (no real tickers) the sleeve is **neutral by construction** — the engine backtest
   returns all-zeros / `insufficient_holdings`, which is the correct "no signal on names it can't see."
   *We do not report a fabricated Sharpe.*

2. **An event study of the tilts** — what the beneficiary basket the sleeve points at actually did,
   window by window, on **real Yahoo prices** — is defensible as a *documented-effect illustration*
   (not a live-tradeable P&L, since it uses the realized window with hindsight on dates):

   - **Ukraine invasion** (24 Feb → 30 Dec 2022), long the REARM+energy beneficiaries
     XLE / ITA / LMT / XOM: **+25.8% basket** vs **−10.2% S&P** → **spread ≈ +36 pts**.
     (XLE +29.5%, LMT +23.1%, XOM +44.1%, ITA +6.7%.)
   - **Red Sea disruption** (15 Dec 2023 → 31 May 2024), long the shipping beneficiaries ZIM / MATX:
     **+73.3% basket** vs **+10.9% S&P** → **spread ≈ +62 pts**.
     (ZIM +124.9%, MATX +21.7%.)

   That is what the *exposure map* captured when the resolution channel fired — the strong channel of
   the whole framework ("trade the resolution, not the forecast"). It is **not** a claim the sleeve
   would have timed the entries: the discipline is that you only take the beneficiary tilt while
   `edge = prob − premium` is positive, and you stand down (Hormuz today) when the premium already
   equals the odds. The event study shows the *size of the move available* when the tilt is right; the
   `edge` gate is what's meant to keep you from paying for it after it's priced.

## Discover more things to price

```bash
python3 -m pari_mutuel_trader.cli discover --category Economics
```

Enumerates what Kalshi is currently pricing, tags each event that maps to a real exposed instrument
(via the keyword→theme map), and prints rows ready to paste into `configs/geopolitical.yaml`. Events
with no tradeable instrument (Sports, Pope) or an un-priceable tail (Mars-by-2050) are counted and
skipped — the filter from `docs/mining-kalshi-for-instruments.md`, made executable.

## Run

```bash
cd pari_mutuel_trader && export PYTHONPATH=src
python3 -m pytest tests/test_geopolitical.py tests/test_kalshi.py tests/test_premium.py -q
python3 -m pari_mutuel_trader.cli discover --category Economics   # find more instruments
# then feed events via configs/geopolitical.yaml and rebuild features before backtest/paper.
```

*Companion: `mispricing-worked-example.md` (the detector and the Hormuz worked example),
`forward-curve-across-conflicts.md`, `live-board-2026.md`. Framework/risk only; not investment advice.*
