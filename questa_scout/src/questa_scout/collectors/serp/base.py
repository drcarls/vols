from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class SerpResult:
    """One organic search result, normalized across backends."""

    link: str
    title: str
    snippet: str = ""


class SerpBackend(Protocol):
    """A source of organic search results for a given query.

    Implementations: BrightDataSerpBackend (live Google via Bright Data
    SERP API) and FixtureBackend (canned JSON for offline runs and tests).

    The same backend serves both the AI-adoption (job-posting) query and the
    governance (LinkedIn-profile) query -- the query string differs, the
    interface does not.
    """

    def search(self, query: str, *, country: str = "us", language: str = "en") -> list[SerpResult]:
        ...
