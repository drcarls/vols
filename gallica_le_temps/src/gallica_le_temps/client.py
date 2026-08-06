"""Thin HTTP client for the Gallica endpoints.

All network access in the package goes through :class:`GallicaClient`. Tests
inject a fake with the same three methods, so nothing else in the package
imports ``requests`` directly.
"""

from __future__ import annotations

import shutil
import subprocess
import time
import urllib.parse
from typing import Optional, Protocol

# Gallica blocks non-browser User-Agents (it returns 403 to the old
# "gallica-le-temps/0.1 …" UA and varies on User-Agent), so present a browser UA.
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


class HttpClient(Protocol):
    """The surface the pipeline needs from an HTTP client."""

    def get_text(self, url: str, params: Optional[dict] = None) -> str: ...

    def get_bytes(self, url: str, params: Optional[dict] = None) -> bytes: ...

    def get_json(self, url: str, params: Optional[dict] = None) -> dict: ...


class GallicaClient:
    """A :mod:`requests`-backed client with polite retry/backoff.

    Gallica asks callers to be gentle; ``min_interval`` throttles requests and a
    small exponential backoff retries transient network/5xx failures. TLS
    verification is left to the environment (e.g. ``REQUESTS_CA_BUNDLE``); it is
    never disabled here.
    """

    def __init__(
        self,
        *,
        session=None,
        min_interval: float = 0.34,
        max_retries: int = 4,
        timeout: float = 60.0,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        import requests  # local import so the package imports without requests

        self._session = session or requests.Session()
        self._session.headers.setdefault("User-Agent", user_agent)
        self._user_agent = user_agent
        self._min_interval = min_interval
        self._max_retries = max_retries
        self._timeout = timeout
        self._last_request_at = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        wait = self._min_interval - elapsed
        if wait > 0:
            time.sleep(wait)

    def _curl_raw(self, url: str, params: Optional[dict]) -> bytes:
        """Fetch via the system ``curl`` — the reliable transport through a
        TLS-reintercepting egress proxy, where ``requests`` cannot complete the
        tunnelled handshake. Honours the same proxy/CA environment."""
        curl = shutil.which("curl")
        if not curl:
            raise RuntimeError("curl unavailable for fallback")
        full = url
        if params:
            full = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        out = subprocess.run(
            [curl, "-sS", "-L", "--http1.1", "--max-time", str(int(self._timeout)),
             "-A", self._user_agent, full],
            capture_output=True, timeout=self._timeout + 10,
        )
        if out.returncode != 0:
            raise RuntimeError(f"curl failed ({out.returncode}): {out.stderr.decode('utf-8','replace')[:200]}")
        return out.stdout

    def _raw(self, url: str, params: Optional[dict]) -> bytes:
        """Return response bytes, trying ``requests`` then ``curl`` per attempt."""
        import requests

        last_exc: Optional[Exception] = None
        for attempt in range(self._max_retries):
            self._throttle()
            try:
                resp = self._session.get(url, params=params, timeout=self._timeout)
                self._last_request_at = time.monotonic()
                if resp.status_code >= 500:
                    raise requests.HTTPError(f"{resp.status_code} for {resp.url}")
                resp.raise_for_status()
                return resp.content
            except requests.RequestException as exc:  # proxy/TLS/network or 5xx
                last_exc = exc
                self._last_request_at = time.monotonic()
                try:  # same attempt, reliable transport
                    return self._curl_raw(url, params)
                except Exception as curl_exc:
                    last_exc = curl_exc
                if attempt == self._max_retries - 1:
                    break
                time.sleep(2 ** attempt)  # 1s, 2s, 4s, ...
        assert last_exc is not None
        raise last_exc

    def get_text(self, url: str, params: Optional[dict] = None) -> str:
        # Gallica ALTO/SRU are UTF-8.
        return self._raw(url, params).decode("utf-8", "replace")

    def get_bytes(self, url: str, params: Optional[dict] = None) -> bytes:
        return self._raw(url, params)

    def get_json(self, url: str, params: Optional[dict] = None) -> dict:
        import json

        return json.loads(self._raw(url, params).decode("utf-8", "replace"))
