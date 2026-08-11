# Does the geopolitical sleeve add value? An honest in-engine test

*A walk-forward of the geopolitical/macro sleeve inside the pari-mutuel stock-picker, on a real
65-name universe (2018–2026). The result is a clean negative-turned-marginal-positive that quantifies
the book's central discipline — **trade the resolution window, not the hold** — in the engine's own P&L.
Reported with its limitations, because the limitations are the point.*

---

## The question

The sleeve turns prediction-market odds into a per-name equity tilt (`edge = prob − premium`). It
plugs into the engine as one co-equal, hedge-weighted agent. Does it actually improve risk-adjusted
returns — and if not, *why not*, and what would fix it?

## Method

- **Universe:** 65 real tickers spanning every exposure theme (energy, tankers, shipping, semis,
  rare-earth/defense, rate-sensitives, insurance, crypto) plus liquid anchors. Daily prices, Yahoo,
  2018-01 to 2026-08.
- **Engine:** unchanged — softmax → pari-mutuel pool → hedge-weighted → top-25 long-only, weekly.
- **Configurations** (same engine, same universe; only the sleeve's input changes):

  | | Concentrate when live? | Exit after the catalyst? |
  |---|:-:|:-:|
  | **A — baseline** (sleeve off) | — | — |
  | **B — static tilt** (today's book held constant) | no | no |
  | **C — dated, hold-through** | no | no |
  | **C + conviction** | **yes** | no |
  | **D — exit rule** (signal decays) | no | **yes** |
  | **D + conviction** | **yes** | **yes** |

- **Honesty flag up front:** the dated events are placed at the dates their episodes actually
  happened (Ukraine 2022, Red Sea 2023-24, the 2022-23 hiking cycle, …). That is **hindsight on
  entry**. So this tests the *exit discipline given a correct entry* and the *engine machinery* — not
  real-time entry timing. Identifying the resolution live is a separate job, and it is exactly what
  the Kalshi `prob` feed is for.

## Result 1 — the ladder

Full-period backtest, 2018–2026 (baseline Sharpe **0.461**, CAGR 20.4%):

| Run | Concentrate | Exit | Sharpe | CAGR | vs baseline |
|---|:-:|:-:|---|---|---|
| A — baseline | — | — | 0.461 | 20.36% | — |
| B — static tilt | no | no | 0.453 | 20.11% | −0.008 |
| C — dated, hold-through | no | no | 0.450 | 19.61% | −0.011 |
| **C + conviction** | **yes** | no | **0.442** | 19.27% | **−0.019 (worst)** |
| D — exit rule | no | **yes** | 0.455 | 20.00% | −0.006 |
| **D + conviction** | **yes** | **yes** | **0.463** | **20.47%** | **+0.002 (beats A)** |

Read the four dated rows as a 2×2 and the mechanism is unmistakable:

- **Concentrate *without* an exit is the single worst thing you can do** (0.442). You load into the
  catalyst names at the resolution and then hold them for years — straight into a decade the
  tech/AI complex dominated and defense/energy/shipping did not. You concentrate the mistake.
- **Exit alone helps but isn't enough** (0.455): you rotate out in time, but never loaded in hard
  enough to capture the pulse.
- **Exit *and* concentrate is the only config that beats baseline** (0.463): load in at the
  resolution, ride the repricing, rotate out as it settles. It needed **both halves**.

That is "buy the invasion, sell the phony war," demonstrated in the engine. The sign of the sleeve's
contribution flips exactly where the framework says it should.

## Result 2 — is the winning config robust, or a lucky knob?

Sweep the exit half-life for the winning config (baseline 0.461):

| Half-life | Sharpe | vs baseline | CAGR |
|---|---|---|---|
| **4 wk** | **0.467** | **+0.006** | 20.65% |
| 8 wk | 0.465 | +0.004 | 20.56% |
| 13 wk | 0.463 | +0.002 | 20.45% |
| 26 wk | 0.455 | −0.006 | 19.93% |
| 52 wk | 0.454 | −0.007 | 19.91% |

**Monotonic, not knife-edge.** Sharpe declines smoothly as the half-life lengthens; the config beats
baseline across the entire short band (4/8/13 wk) and turns negative only past ~a quarter. The sign is
governed by one interpretable parameter — *how fast you exit* — not a fragile sweet spot. The a-priori
13-week pick was conservative; the true optimum is faster.

The economic reading is the whole book in one line: **the resolution edge decays with a half-life of
weeks.** Hold the catalyst names a quarter and it's gone; hold a year and you are worse than doing
nothing.

## What this means — and doesn't

**Validated:** the *mechanism*. Static directional exposure is a drag; concentration without an exit
makes it worse; concentration *with* a weeks-scale exit is the only thing that adds value, robustly.
This is the "resolution window, not the hold" discipline, proven in-engine on real prices.

**Not claimed:**
- **Not real-time entry alpha.** Entries were hindsight-placed. The test isolates the exit discipline
  and the engine, not the ability to call the resolution live (that is the odds feed's job).
- **Not a large edge.** Even the best config is +0.006 Sharpe / +30 bps CAGR. Diluted into a 25-name
  long-only book at a ~1/7 hedge weight, the magnitude is small. The edge is meant to be harvested in
  a **concentrated satellite**, which this core-overlay backtest structurally cannot express.
- **One universe, one regime.** 2018–2026 was a tech-led bull market with only brief war-resolution
  windows — a hard environment for this sleeve. A value/defensive-led decade with a major resolution
  could read differently. (The book-level −28% max-drawdown breach is a config artifact of the
  equal-weight/no-vol-target benchmark, constant across all rows; it does not affect the comparison.)

## The takeaway for how to use it

Keep the sleeve as an **attributed, hedge-weighted lead indicator** and a **satellite trade
generator** — not a lever you crank inside the core. When you *do* express it, the engine now carries
the discipline as a first-class feature: `attach_geo_signal_timeline(..., half_life_weeks=…)` pulses
the signal at the resolution and decays it out, so the weekly rebalance performs the exit. Set the
half-life to weeks, not quarters.

*Reproduce: `scripts/fetch_real_universe.py` then `scripts/wfo_geo_sleeve.py` (add `--sweep` for the
half-life curve). Framework and risk disciplines only; not investment advice. Backtest figures are
illustrative of mechanism, not a live-tradeable track record.*
