"""Thin HTTP client for the Gallica endpoints.

All network access in the package goes through :class:`GallicaClient`. Tests
inject a fake with the same three methods, so nothing else in the package
imports ``requests`` directly.
"""

from __future__ import annotations

import time
from typing import Optional, Protocol

DEFAULT_USER_AGENT = (
    "gallica-le-temps/0.1 (research; locate-with-text extraction of Le Temps)"
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
        self._min_interval = min_interval
        self._max_retries = max_retries
        self._timeout = timeout
        self._last_request_at = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        wait = self._min_interval - elapsed
        if wait > 0:
            time.sleep(wait)

    def _request(self, url: str, params: Optional[dict]):
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
                return resp
            except (requests.RequestException,) as exc:  # network or 5xx
                last_exc = exc
                self._last_request_at = time.monotonic()
                if attempt == self._max_retries - 1:
                    break
                time.sleep(2 ** attempt)  # 1s, 2s, 4s, ...
        assert last_exc is not None
        raise last_exc

    def get_text(self, url: str, params: Optional[dict] = None) -> str:
        resp = self._request(url, params)
        # Gallica ALTO/SRU are UTF-8; let requests honour the declared charset.
        return resp.text

    def get_bytes(self, url: str, params: Optional[dict] = None) -> bytes:
        return self._request(url, params).content

    def get_json(self, url: str, params: Optional[dict] = None) -> dict:
        return self._request(url, params).json()
