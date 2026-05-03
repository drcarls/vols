SHELL := /bin/bash
PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python
STREAMLIT := $(VENV)/bin/streamlit
UVICORN := $(VENV)/bin/uvicorn

.DEFAULT_GOAL := help

.PHONY: help setup install doctor build-features backtest wfo paper ui api test open-dashboard build-macos-app install-macos-app clean

help:
	@echo "pari_mutuel_trader shortcuts"
	@echo "  make setup          # create venv + install deps + editable package"
	@echo "  make doctor         # environment diagnostics"
	@echo "  make build-features # build local features parquet"
	@echo "  make backtest       # run backtest with default config"
	@echo "  make wfo            # run walk-forward optimization"
	@echo "  make paper          # run paper state update"
	@echo "  make ui             # launch Streamlit dashboard"
	@echo "  make api            # launch FastAPI server"
	@echo "  make test           # run pytest"
	@echo "  make open-dashboard # open Finder launcher"
	@echo "  make build-macos-app # build PariMutuelTrader.app in dist/"
	@echo "  make install-macos-app # install app to ~/Applications"

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

install: setup

doctor:
	$(PY) -m pari_mutuel_trader.cli doctor

build-features:
	$(PY) -m pari_mutuel_trader.cli build-features --config configs/default.yaml

backtest:
	$(PY) -m pari_mutuel_trader.cli backtest --config configs/default.yaml

wfo:
	$(PY) -m pari_mutuel_trader.cli wfo --config configs/wfo.yaml

paper:
	$(PY) -m pari_mutuel_trader.cli paper-run --config configs/default.yaml

ui:
	$(STREAMLIT) run src/pari_mutuel_trader/ui/streamlit_app.py

api:
	$(UVICORN) pari_mutuel_trader.api.main:app --reload

test:
	PYTHONPATH=src $(PY) -m pytest -q

open-dashboard:
	open run_dashboard.command

build-macos-app:
	bash scripts/build_macos_app.sh

install-macos-app:
	bash install_macos.command

clean:
	rm -rf $(VENV) .pytest_cache
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
