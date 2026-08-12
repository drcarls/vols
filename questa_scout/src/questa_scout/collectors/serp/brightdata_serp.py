from __future__ import annotations

"""Bright Data SERP API backend.

Uses Bright Data's Direct API endpoint to run a Google search and return
parsed results. Docs: https://docs.brightdata.com/scraping-automation/serp-api

Requires:
  - BRIGHTDATA_API_TOKEN  (Bearer token; read from env, never committed)
  - a SERP zone name (default "serp"), configurable

Cost at our volume is negligible: two requests per company (one jobs query,
one governance query), ~$1.50/1000 requests PAYG with a 5k/month free tier.
Failed requests aren't billed.
"""

import json
from urllib.parse import urlencode

from .base import SerpResult

BRIGHTDATA_API_URL = "https://api.brightdata.com/request"


class BrightDataSerpBackend:
    def __init__(self, token: str, zone: str = "serp", timeout: int = 30):
        if not token:
            raise ValueError("Bright Data API token is required for live SERP queries")
        self.token = token
        self.zone = zone
        self.timeout = timeout

    def _google_url(self, query: str, country: str, language: str) -> str:
        params = {
            "q": query,
            "gl": country,      # geo-target (us)
            "hl": language,     # interface language (en)
            "num": "20",
            "brd_json": "1",    # ask Bright Data to return parsed JSON
        }
        return "https://www.google.com/search?" + urlencode(params)

    def search(self, query: str, *, country: str = "us", language: str = "en") -> list[SerpResult]:
        import requests  # imported lazily so fixture-only runs need no dependency

        payload = {
            "zone": self.zone,
            "url": self._google_url(query, country, language),
            "format": "raw",
        }
        resp = requests.post(
            BRIGHTDATA_API_URL,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return parse_serp_json(resp.text)


def parse_serp_json(raw: str | dict) -> list[SerpResult]:
    """Parse a Bright Data SERP JSON payload into normalized results.

    Kept as a module-level function so it can be unit-tested against saved
    fixtures without any network access.
    """
    data = json.loads(raw) if isinstance(raw, str) else raw
    organic = data.get("organic") or data.get("organic_results") or []
    results: list[SerpResult] = []
    for item in organic:
        link = item.get("link") or item.get("url") or ""
        title = item.get("title") or ""
        snippet = item.get("description") or item.get("snippet") or ""
        if link:
            results.append(SerpResult(link=link, title=title, snippet=snippet))
    return results
