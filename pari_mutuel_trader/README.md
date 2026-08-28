# pari_mutuel_trader

V1 local trading research app for a long-only weekly US equities stock-picker using multi-agent pari-mutuel aggregation.

## Fastest setup (Makefile)

```bash
cd pari_mutuel_trader
make setup
make doctor
make backtest
```

Other shortcuts:

```bash
make build-features
make wfo
make paper
make ui
make api
make test
```

## One-click macOS launcher

You can double-click `run_dashboard.command` in Finder to open the dashboard.

- On first run it will call `make setup` automatically.
- Then it starts Streamlit via `make ui`.

```bash
open run_dashboard.command
```

## Install like a normal macOS app (double-click from Applications)

From Terminal once:

```bash
cd pari_mutuel_trader
make install-macos-app
```

This creates `PariMutuelTrader.app` and installs it to `~/Applications`.
After that you can launch by double-clicking the app icon in Finder.

## Manual setup (if preferred)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

## CLI commands

```bash
python -m pari_mutuel_trader.cli doctor
python -m pari_mutuel_trader.cli build-features
python -m pari_mutuel_trader.cli backtest --config configs/default.yaml
python -m pari_mutuel_trader.cli wfo --config configs/wfo.yaml
python -m pari_mutuel_trader.cli paper-run --config configs/default.yaml
python -m pari_mutuel_trader.cli review-positions --positions configs/positions.example.yaml
```

## Valuation and sell discipline

The picker decides what to own. This layer decides what a position is still worth
holding, and at what size, once it has run.

### IV15 and IV8

Both are the same discounted owner-earnings model read at two hurdle rates, so a
single set of assumptions produces both:

- **IV15** - the price at which the business is priced to return 15%. Capital goes
  to work at or below it.
- **IV8** - the price at which it returns 8%. Past this the business has stopped
  earning its keep for a holder.

Growth is not free in the model: sustaining growth `g` consumes `g / ROIC` of
earnings, so only the remainder is owner cash. A high and *enduring* ROIC is what
converts growth into value, which is why competitive position and ROIC are inputs
to the valuation rather than a separate score bolted onto it. Together they set:

- the **competitive advantage period** - how many years the business compounds
  before fading (5 years for a commodity, up to 15 for a wide-moat franchise),
- the **terminal ROIC** - returns decay toward the cost of capital, and only a
  durable franchise keeps part of the spread.

Four zones follow from where the price sits:

| zone | condition | weight ceiling |
| --- | --- | --- |
| `spring_loaded` | at or below IV15 | conviction weight (8%) |
| `fair` | between IV15 and IV8 | core weight (6%) |
| `rich` | past IV8, inside the rich band | 4.5% |
| `expensive` | past IV8 by more than the band | house-money weight (3%) |

Two asymmetries are deliberate. Being at IV15 is enough to *keep* a full position
but not to *build* one - adds happen at the **add level**, which demands the
required return plus a margin. And a spring-loaded name that has grown past the
conviction weight through appreciation is left alone: the ceiling governs
purchases, not winners.

### Selling is an after-tax decision

The nominal price is not what is realized. Tax takes 20-50% of the gain, so every
decision is scored on the **after-tax price** and on the hurdle it implies:

```
required replacement return = (1 + return on holding) x (gross / after-tax)^(1/horizon) - 1
```

A replacement idea has to clear that hurdle, plus a margin, before capital moves.
This is what lets a position be trimmed while it is still *fair* - nothing is
wrong with it, the capital is simply worth more elsewhere - and equally what stops
a marginally better idea from paying for its own tax bill. Held at a loss, the
shelter runs the other way and the hurdle falls below the holding's own return.

The deferral runs one way only. Waiting out the clock to a long-term rate is
flagged as defensible when a position is merely rich and close to the year mark;
in an expensive position it is not, and the review says so.

### What comes out

A `trim` rather than a binary sell is the usual answer. A rich but durable
franchise keeps a house-money stake; only a rich name with a *thin* moat is closed
outright. The review reports whether the after-tax proceeds have returned the
original cost - the point at which the remaining stake is house money - and routes
the harvested capital into the most spring-loaded names on the watchlist, capped
at the conviction weight so one trim cannot rebuild an oversized position
elsewhere.

```bash
python -m pari_mutuel_trader.cli review-positions --positions configs/positions.example.yaml
python -m pari_mutuel_trader.cli review-positions --positions my_book.yaml --json
```

Positions, tax rates and policy live in one YAML file - see
`configs/positions.example.yaml` for the schema and for what each assumption
means. `--as-of` overrides the date used for the holding-period test.

The same zones feed the picker as a `ValuationAgent` and as a weight overlay in
the backtest, both of which degrade to neutral when a feature frame carries no
`discount_to_iv15` / `premium_to_iv8` columns. `make paper` writes the review into
the dashboard state, where it surfaces in the Streamlit app and at
`/position_review` and `/redeploy_plan`.

## UI + API

```bash
streamlit run src/pari_mutuel_trader/ui/streamlit_app.py
uvicorn pari_mutuel_trader.api.main:app --reload
```

## Notes

- V1 runs on local CSV/parquet fallback data; no API keys required.
- News and macro agents degrade gracefully to neutral when data is missing.
- `lead_lag` is scaffolded for future cross-asset/time-zone extension.
- The valuation layer runs on assumptions you supply; it does not fetch fundamentals.
  The zones and hurdles are only as good as the owner earnings, growth and ROIC behind them.
