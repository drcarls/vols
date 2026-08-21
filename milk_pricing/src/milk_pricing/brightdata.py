"""Bright Data collection clients.

Two independent paths, because Instacart splits across both:

* `WebUnlocker` — POST /request. Renders JS and returns page HTML. Needed for
  Instacart search and aisle pages, which ship an empty shell and populate
  client-side.
* `DatasetAPI` — the v3 trigger/progress/snapshot cycle against a prebuilt
  Instacart scraper. Higher latency and asynchronous, but it handles pagination
  and geo pinning for us on large pulls.

The token is read from the environment only. Nothing here ever persists a
credential to disk or to the collected output.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

API_ROOT = "https://api.brightdata.com"


class BrightDataError(RuntimeError):
    pass


def _token() -> str:
    tok = os.environ.get("BRIGHTDATA_API_TOKEN", "").strip()
    if not tok:
        raise BrightDataError(
            "BRIGHTDATA_API_TOKEN is not set. Export it before collecting:\n"
            "  export BRIGHTDATA_API_TOKEN='...'\n"
            "It is read from the environment only and never written to disk."
        )
    return tok


def _post(path: str, payload: dict, timeout: int = 180) -> tuple[int, bytes]:
    req = urllib.request.Request(
        f"{API_ROOT}{path}",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {_token()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def _get(path: str, timeout: int = 180) -> tuple[int, bytes]:
    req = urllib.request.Request(
        f"{API_ROOT}{path}",
        headers={"Authorization": f"Bearer {_token()}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


@dataclass
class WebUnlocker:
    """Fetch one rendered page through a Bright Data Web Unlocker zone."""

    zone: str = os.environ.get("BRIGHTDATA_ZONE", "web_unlocker1")
    max_retries: int = 3

    def fetch(self, url: str, country: str = "us") -> str:
        """Return rendered HTML. Retries transient 5xx with linear backoff."""
        payload = {
            "zone": self.zone,
            "url": url,
            "format": "raw",
            "country": country,
        }
        last = ""
        for attempt in range(1, self.max_retries + 1):
            status, body = _post("/request", payload)
            if status == 200:
                return body.decode("utf-8", errors="replace")
            last = body.decode("utf-8", errors="replace")[:400]
            if status in (401, 403):
                # Auth and policy failures never succeed on retry.
                raise BrightDataError(f"Bright Data auth/policy error {status}: {last}")
            time.sleep(2 * attempt)
        raise BrightDataError(f"Web Unlocker failed after {self.max_retries} tries: {last}")

    def verify(self) -> str:
        """Cheap credential check against a stable endpoint."""
        status, body = _get("/status")
        if status == 200:
            return "ok"
        raise BrightDataError(
            f"Token rejected ({status}): {body.decode('utf-8', 'replace')[:200]}")


@dataclass
class DatasetAPI:
    """Trigger and drain a prebuilt Bright Data scraper snapshot."""

    dataset_id: str
    poll_seconds: int = 15
    timeout_seconds: int = 1800

    def trigger(self, inputs: list[dict]) -> str:
        status, body = _post(
            f"/datasets/v3/trigger?dataset_id={self.dataset_id}&include_errors=true",
            inputs,
        )
        if status not in (200, 202):
            raise BrightDataError(
                f"trigger failed ({status}): {body.decode('utf-8','replace')[:300]}")
        sid = json.loads(body).get("snapshot_id")
        if not sid:
            raise BrightDataError(f"no snapshot_id in response: {body[:200]!r}")
        return sid

    def wait(self, snapshot_id: str) -> None:
        deadline = time.time() + self.timeout_seconds
        while time.time() < deadline:
            status, body = _get(f"/datasets/v3/progress/{snapshot_id}")
            if status != 200:
                raise BrightDataError(f"progress failed ({status})")
            state = json.loads(body).get("status")
            if state == "ready":
                return
            if state in ("failed", "canceled"):
                raise BrightDataError(f"snapshot {snapshot_id} ended: {state}")
            time.sleep(self.poll_seconds)
        raise BrightDataError(f"snapshot {snapshot_id} not ready within timeout")

    def download(self, snapshot_id: str) -> list[dict]:
        status, body = _get(f"/datasets/v3/snapshot/{snapshot_id}?format=json")
        if status != 200:
            raise BrightDataError(f"download failed ({status})")
        text = body.decode("utf-8", errors="replace").strip()
        if not text:
            return []
        try:
            data = json.loads(text)
            return data if isinstance(data, list) else [data]
        except json.JSONDecodeError:
            # Snapshots are sometimes newline-delimited JSON.
            return [json.loads(ln) for ln in text.splitlines() if ln.strip()]

    def collect(self, inputs: list[dict]) -> list[dict]:
        sid = self.trigger(inputs)
        self.wait(sid)
        return self.download(sid)


# The trigger payload the prebuilt Instacart scraper expects, one row per
# retailer x ZIP. Kept as a function so `collect.py` stays declarative.
def instacart_inputs(retailer_slug: str, zips: list[str], keyword: str = "milk") -> list[dict]:
    return [
        {
            "url": f"https://www.instacart.com/store/{retailer_slug}/s?k={keyword}",
            "zip_code": z,
            "keyword": keyword,
        }
        for z in zips
    ]
