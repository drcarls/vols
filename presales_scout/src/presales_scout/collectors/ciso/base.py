from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class SerpResult:
    """One organic search result, normalized across backends."""

    link: str
    title: str
    snippet: str = ""


class CisoBackend(Protocol):
    """A source of organic search results for a given query.

    Implementations: BrightDataSerpBackend (live Google via Bright Data
    SERP API) and FixtureBackend (canned JSON for offline runs and tests).
    """

    def search(self, query: str, *, country: str = "se", language: str = "sv") -> list[SerpResult]:
        ...
