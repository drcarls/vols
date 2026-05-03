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
```

## UI + API

```bash
streamlit run src/pari_mutuel_trader/ui/streamlit_app.py
uvicorn pari_mutuel_trader.api.main:app --reload
```

## Notes

- V1 runs on local CSV/parquet fallback data; no API keys required.
- News and macro agents degrade gracefully to neutral when data is missing.
- `lead_lag` is scaffolded for future cross-asset/time-zone extension.
