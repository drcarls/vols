"""Shared fixtures.

Each test gets an isolated on-disk SQLite database. The environment variables
are set before any app module is imported, because ``app.db.base`` builds its
engine at import time from settings.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

_TEST_DB = REPO_ROOT / "data" / "test_domain_arbitrage.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TEST_DB}")
os.environ.setdefault("ALLOW_FIXTURE_DATA", "true")
os.environ.setdefault("LLM_PROVIDER", "null")

from app.db.base import session_scope  # noqa: E402
from app.db.init_db import reset_db  # noqa: E402
from app.services.ingest import ingest_csv  # noqa: E402
from app.services.pipeline import run_pipeline  # noqa: E402

EXAMPLE_CSV = REPO_ROOT / "data" / "examples" / "domains_example.csv"
EXAMPLE_KEYWORDS = REPO_ROOT / "data" / "examples" / "keywords_EXAMPLE_SYNTHETIC.csv"
EXAMPLE_COMPANIES = REPO_ROOT / "data" / "examples" / "companies_EXAMPLE_SYNTHETIC.csv"


@pytest.fixture
def db():
    reset_db()
    with session_scope() as session:
        yield session


@pytest.fixture
def scored_db():
    """A database with the example CSV imported and one pipeline run complete."""
    reset_db()
    with session_scope() as session:
        ingest_csv(session, EXAMPLE_CSV, source_label="test")
    with session_scope() as session:
        run_pipeline(session)
    with session_scope() as session:
        yield session
