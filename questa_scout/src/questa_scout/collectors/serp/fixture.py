from __future__ import annotations

"""Offline SERP backend backed by saved JSON fixtures.

Lets the whole pipeline (and the test suite) run with no Bright Data token
and no network. Fixtures live in two subdirectories of ``fixtures/serp``:

  fixtures/serp/adoption/<slug>.json     -- job-posting query results
  fixtures/serp/governance/<slug>.json   -- LinkedIn-profile query results

The backend picks the subdirectory from the query (a jobs query targets
``linkedin.com/jobs``; a governance query targets ``linkedin.com/in``),
keyed by a slug of the company name. Unknown companies return an empty
result set (which the collectors read as "none found").
"""

import re
from pathlib import Path

from .base import SerpResult
from .brightdata_serp import parse_serp_json


def slug(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def _subdir_for(query: str) -> str:
    q = query.lower()
    if "linkedin.com/jobs" in q:
        return "adoption"
    return "governance"


class FixtureBackend:
    def __init__(self, fixtures_path: Path):
        self.fixtures_path = Path(fixtures_path)

    def search(self, query: str, *, country: str = "us", language: str = "en") -> list[SerpResult]:
        # Recover the company name from the query's trailing quoted term.
        m = re.search(r'"([^"]+)"\s*$', query)
        key = slug(m.group(1)) if m else ""
        path = self.fixtures_path / _subdir_for(query) / f"{key}.json"
        if not path.exists():
            return []
        return parse_serp_json(path.read_text(encoding="utf-8"))
