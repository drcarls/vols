"""Minimal HTTP fetcher for discovery.

Only used for robots.txt. Flow capture goes through a real browser, because a
checkout page's prices are rendered, not served.
"""

from __future__ import annotations

import urllib.error
import urllib.request

from .politeness import Policy, user_agent

_BASE_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


class UrllibFetcher:
    """Honest identification, no redirect chasing beyond the default, short timeout."""

    def __init__(self, policy: Policy, timeout: float = 20.0) -> None:
        self._ua = user_agent(_BASE_UA, policy)
        self._timeout = timeout

    def get(self, url: str) -> tuple[int, str]:
        request = urllib.request.Request(url, headers={"User-Agent": self._ua})
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
                return response.status, body
        except urllib.error.HTTPError as exc:
            # A 404 or 403 on robots.txt is a result worth recording, not a crash.
            return exc.code, ""
