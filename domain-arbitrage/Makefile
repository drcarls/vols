.PHONY: help install demo test serve load-test sensitivity clean reset

VENV ?= .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip

help:
	@echo "install    create the virtualenv and install dependencies"
	@echo "demo       run the full pipeline on the bundled example data"
	@echo "test       run the test suite"
	@echo "serve      start the API and dashboard on :8000"
	@echo "load-test  generate 10,000 synthetic domains and time a full run"
	@echo "sensitivity  sweep the priors and ablate the ranking components"
	@echo "reset      drop and recreate the database (destructive)"
	@echo "clean      remove caches and the generated database"

install:
	python3.12 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt

demo:
	$(PY) scripts/run_demo.py

test:
	$(PY) -m pytest tests/ -q

serve:
	$(VENV)/bin/uvicorn app.main:app --reload --port 8000

load-test:
	$(PY) scripts/generate_test_csv.py 10000 data/load_test_SYNTHETIC.csv
	$(PY) scripts/load_test.py

sensitivity:
	$(PY) scripts/sensitivity.py

reset:
	$(PY) -c "import sys; sys.path.insert(0,'.'); from app.db.init_db import reset_db; reset_db(); print('database reset')"

clean:
	rm -rf .pytest_cache **/__pycache__ data/*.db data/*.db-wal data/*.db-shm
