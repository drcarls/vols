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

`make paper` writes the review into the dashboard state, where it surfaces in the
Streamlit app and at `/position_review` and `/redeploy_plan`.

## The same discipline inside a strategy sleeve

A concentrated book and a 25-name weekly sleeve need the same discipline in
different units. Three things change on the way across.

### Ceilings are relative, not absolute

Absolute ceilings are portfolio percentages, which is the right unit for a book
where a single name runs to 18%. In a sleeve the natural position is `1 / top_k` -
4% at 25 names - so every absolute ceiling above that is inert and the overlay can
only ever shave the expensive bucket. Setting `valuation.sizing: relative` scales
the ceilings off the natural position instead:

| zone | multiple | at 25 names | at 50 names |
| --- | --- | --- | --- |
| `spring_loaded` | 1.6x | 6.4% | 3.2% |
| `fair` | 1.15x | 4.6% | 2.3% |
| `rich` | 0.8x | 3.2% | 1.6% |
| `expensive` | 0.5x | 2.0% | 1.0% |

All four bind at any breadth. Keep `absolute` for the concentrated book - which is
what `configs/positions.example.yaml` does.

### The agent abstains rather than voting flat

`ValuationAgent` returns no vote when a feature frame carries no intrinsic value
data, and abstaining agents are dropped from the pool. A flat vote is not neutral:
it dilutes the agents that do have a view. With abstention a sleeve without
fundamentals scores exactly as it did before the agent existed.

### Tax is charged where the sleeve actually pays it

A weekly sleeve realizes essentially everything short-term, and the pre-tax equity
curve says nothing about that. The backtest now keeps a lot ledger - entry price,
entry date, relieved highest-cost-first - and reports an after-tax curve beside the
pre-tax one, with `CAGR_after_tax`, `tax_drag_annual` and
`short_term_share_of_tax`.

Two corrections matter more than the headline:

- **Wash sales.** A rotating sleeve sells losers constantly and buys some back
  within weeks. Booking those losses as credits reports a tax benefit the holder
  never receives. A repurchase inside 30 days disallows the loss and rolls it into
  the replacement lot's basis.
- **Seasoning.** A sale is deferred when the position is within `wait_days` of
  long-term treatment, sits on a gain, and is still inside `keep_multiple x top_k`
  by score. Once conviction goes the clock stops being a reason to stay. Note that
  this rule is close to inert at weekly cadence - nothing is held long enough to
  approach the one-year mark - and only starts to matter at quarterly or slower.

Both are configured under `tax_aware` and can be switched off individually.

## The dislocated quality sleeve

Durable franchises whose price has fallen further than their value. This is the
sleeve the valuation layer was built for, and it is where the layer stops being an
overlay and becomes the selection engine.

```bash
make dq   # build features with valuation attached, then run the sleeve
```

Three things separate it from the momentum sleeve.

**A hard quality gate.** `portfolio.min_durability` drops names below the
threshold from the universe before anything is scored. This is a gate, not a tilt:
buying a fallen price is only a strategy when the business behind it will still be
there, and below the line a discount is just a discount.

**Dislocation, not weakness.** The signal is the price fall *in excess of* the fall
in intrinsic value over the window. A name whose value fell as fast as its price
deteriorated rather than dislocated, and scores zero. That distinction needs value
to be its own series, so `configs/fundamentals.example.yaml` accepts dated
revisions per symbol and `attach_valuation` forward-fills them onto the price
frame. Without revisions the discount is just a restatement of past price.

**A slower clock.** `backtest.rebalance_days` sets the cadence in sessions - 5 is
weekly, 63 roughly quarterly. Positions bought on weakness need time to work.

This sleeve ships as a 401(k) sleeve (`tax.status: tax_deferred`), which removes
the other half of that argument. In a taxable account the cadence pays for itself
on tax alone - slowing the clock converts short-term gains into long-term ones,
taking the drag from 4.32% weekly with 80% of tax short-term to 1.01% annual with
36%, and only past a quarterly cadence does anything survive long enough for the
holding-period rule to fire. Inside the wrapper that column is zero at every
cadence, and the only friction left is trading cost:

| cadence | cost drag at 10bp | tax drag (401k) | tax drag (taxable) |
| --- | --- | --- | --- |
| weekly | 0.46% | 0.00% | 4.32% |
| monthly | 0.29% | 0.00% | 4.43% |
| quarterly | 0.13% | 0.00% | 2.79% |
| annual | 0.06% | 0.00% | 1.01% |

So in a retirement wrapper the cadence is a claim about how fast the signal decays
and what trading costs, and nothing else. Returns in these sweeps are not evidence
of anything - the sample universe is a random walk.

The sleeve's roster is set by `learning.agents`, so it runs on
`dislocated_quality`, `valuation`, `low_vol` and `house` rather than the V1 set.
`DislocatedQualityAgent` votes against momentum by construction, which is the
point of having it in the pool.

## Where each piece belongs in a multi-sleeve account

The three parts of this layer sit at three different levels, and the level decides
where each is configured.

**The IV15/IV8 model is an enhancer.** It attaches to any sleeve whose names have
fundamentals behind them, and it is configured *per sleeve*, because a
concentrated book and a diversified sleeve want different units - `absolute` for
one, `relative` for the other. A systematic sleeve with no fundamentals simply
gets no valuation opinion: the agent abstains and the overlay does not bind.

**The conviction book is a sleeve.** It is not an overlay on anything; it is a peer
of the systematic sleeve with its own allocation, holdings and policy.

**The tax discipline is neither.** Tax follows the taxpayer, not the strategy, so
lot relief, wash sales and loss offsets belong to the account and are configured
once. Modelling them per sleeve gets three things wrong, which is exactly what the
account level checks:

| check | what a sleeve sees | what the account sees |
| --- | --- | --- |
| look-through exposure | its own 6% position | 13.7% of the same name across two sleeves that each sized it correctly |
| wash sales | it never repurchased | a *different* sleeve bought the ticker inside 30 days, disallowing the loss |
| opportunity set | its own watchlist | every spring-loaded name the account can reach |

That last one matters for the switch test. A trim is only honest if the
alternative it is measured against is the best the account can reach, not merely
the best the book happens to track.

### Wrappers

`tax.status` is `taxable`, `tax_deferred` (401k, traditional IRA) or `tax_free`
(Roth), set on the account and overridable per sleeve with `tax_status`. Inside a
retirement wrapper no sale is a taxable event, so every rate is zero and the whole
after-tax apparatus has nothing to bite on:

- the replacement hurdle collapses to the return on offer, so a switch that tax
  blocked in a taxable account goes straight through;
- the holding-period clock stops mattering, and the seasoning rule is disabled;
- there are no losses to wash, and none to harvest either.

One thing gets *worse* across wrappers rather than better. A loss realized in a
taxable sleeve and washed by a purchase in a retirement sleeve cannot roll into
the replacement lot's basis, so the deduction is lost permanently rather than
deferred (IRS Rev. Rul. 2008-5 - worth confirming with your own advisor). The
account review reports those conflicts first and labels them `permanent`.

Because tax is usually the dominant friction, removing it leaves a backtest with
none at all. `portfolio.cost_bps` charges round-trip spread and impact against
notional traded so a sheltered sleeve is not tuned against a frictionless world;
metrics report `CAGR_gross`, `CAGR` net of cost, and `CAGR_after_tax`.

```bash
python -m pari_mutuel_trader.cli review-account --account configs/account.example.yaml
```

See `configs/account.example.yaml` for the schema. The example deliberately
overlaps two books so the cross-sleeve checks have something to find; the
single-strategy path is untouched, and a sleeve list is optional.

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
