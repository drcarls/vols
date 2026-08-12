from __future__ import annotations

"""Offline SERP backend backed by saved JSON fixtures.

Lets the whole pipeline (and the test suite) run with no Bright Data token
and no network. Fixtures live in fixtures/serp/<key>.json in Bright Data's
SERP JSON shape, keyed by a slug of the company name. Unknown companies
return an empty result set (which the detector reads as "none found").
"""

import re
from pathlib import Path

from .base import SerpResult
from .brightdata_serp import parse_serp_json


def slug(name: str) -> str:
    s = name.lower()
    for a, b in (("å", "a"), ("ä", "a"), ("ö", "o")):
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


class FixtureBackend:
    def __init__(self, fixtures_path: Path):
        self.fixtures_path = Path(fixtures_path)

    def search(self, query: str, *, country: str = "se", language: str = "sv") -> list[SerpResult]:
        # Recover the company name from the query's trailing quoted term.
        m = re.search(r'"([^"]+)"\s*$', query)
        key = slug(m.group(1)) if m else ""
        path = self.fixtures_path / f"{key}.json"
        if not path.exists():
            return []
        return parse_serp_json(path.read_text(encoding="utf-8"))
