"""Thin, dependency-light client for Bright Data.

Supports the two Bright Data products that are relevant to Instacart:

1. Web Scraper API (Datasets v3)  -- RECOMMENDED for Instacart.
   Bright Data maintains a managed Instacart collector that returns clean,
   structured product/price JSON and handles the location/zip gating and
   anti-bot layer for you. You give it Instacart URLs (+ a zip code) and it
   returns rows. This is by far the most reliable path.

2. Web Unlocker API -- a general "give me the HTML for this URL" unlocker.
   Useful as a fallback / DIY path, but you then have to parse Instacart's
   markup yourself, and Instacart is heavily geo-gated and JS-rendered, so
   this path is best-effort.

All credentials come from environment variables (see .env.example) so nothing
secret is hard-coded or committed.
"""

from __future__ import annotations

import os
import time
from typing import Any, Iterable

import requests


class BrightDataError(RuntimeError):
    """Raised for any Bright Data API / configuration problem."""


class BrightDataClient:
    UNLOCKER_URL = "https://api.brightdata.com/request"
    TRIGGER_URL = "https://api.brightdata.com/datasets/v3/trigger"
    PROGRESS_URL = "https://api.brightdata.com/datasets/v3/progress/{snapshot_id}"
    SNAPSHOT_URL = "https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}"

    def __init__(
        self,
        api_token: str | None = None,
        unlocker_zone: str | None = None,
        dataset_id: str | None = None,
        timeout: int = 90,
    ) -> None:
        self.api_token = api_token or os.getenv("BRIGHTDATA_API_TOKEN")
        self.unlocker_zone = unlocker_zone or os.getenv("BRIGHTDATA_UNLOCKER_ZONE")
        self.dataset_id = dataset_id or os.getenv("BRIGHTDATA_INSTACART_DATASET_ID")
        self.timeout = timeout

        if not self.api_token:
            raise BrightDataError(
                "BRIGHTDATA_API_TOKEN is not set. Copy .env.example to .env and fill it in."
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
        )

    # ------------------------------------------------------------------ #
    # Web Unlocker
    # ------------------------------------------------------------------ #
    def unlock(self, url: str, country: str = "us", data_format: str = "raw") -> str:
        """Fetch a single URL through the Web Unlocker zone. Returns raw text."""
        if not self.unlocker_zone:
            raise BrightDataError(
                "BRIGHTDATA_UNLOCKER_ZONE is required to use the Web Unlocker path."
            )
        payload = {
            "zone": self.unlocker_zone,
            "url": url,
            "format": data_format,
            "country": country,
        }
        resp = self.session.post(self.UNLOCKER_URL, json=payload, timeout=self.timeout)
        if resp.status_code >= 400:
            raise BrightDataError(
                f"Web Unlocker request failed ({resp.status_code}): {resp.text[:500]}"
            )
        return resp.text

    # ------------------------------------------------------------------ #
    # Web Scraper API (Datasets v3)
    # ------------------------------------------------------------------ #
    def trigger_dataset(
        self,
        inputs: list[dict[str, Any]],
        extra_params: dict[str, str] | None = None,
    ) -> str:
        """Kick off a collection. Returns a snapshot_id to poll."""
        if not self.dataset_id:
            raise BrightDataError(
                "BRIGHTDATA_INSTACART_DATASET_ID is required to use the Web Scraper API path."
            )
        params = {"dataset_id": self.dataset_id, "include_errors": "true"}
        if extra_params:
            params.update(extra_params)

        resp = self.session.post(
            self.TRIGGER_URL, params=params, json=inputs, timeout=self.timeout
        )
        if resp.status_code >= 400:
            raise BrightDataError(
                f"Dataset trigger failed ({resp.status_code}): {resp.text[:500]}"
            )
        data = resp.json()
        snapshot_id = data.get("snapshot_id")
        if not snapshot_id:
            raise BrightDataError(f"No snapshot_id returned from trigger: {data}")
        return snapshot_id

    def snapshot_status(self, snapshot_id: str) -> str:
        resp = self.session.get(
            self.PROGRESS_URL.format(snapshot_id=snapshot_id), timeout=self.timeout
        )
        if resp.status_code >= 400:
            raise BrightDataError(
                f"Progress check failed ({resp.status_code}): {resp.text[:500]}"
            )
        return resp.json().get("status", "unknown")

    def wait_for_snapshot(
        self, snapshot_id: str, poll_interval: int = 10, max_wait: int = 1800
    ) -> None:
        """Block until the snapshot is ready. Raises on failure/timeout."""
        elapsed = 0
        while elapsed < max_wait:
            status = self.snapshot_status(snapshot_id)
            if status == "ready":
                return
            if status in ("failed", "error"):
                raise BrightDataError(f"Snapshot {snapshot_id} ended with status={status}")
            time.sleep(poll_interval)
            elapsed += poll_interval
        raise BrightDataError(
            f"Snapshot {snapshot_id} not ready after {max_wait}s (last status polled)."
        )

    def fetch_snapshot(self, snapshot_id: str, data_format: str = "json") -> Any:
        resp = self.session.get(
            self.SNAPSHOT_URL.format(snapshot_id=snapshot_id),
            params={"format": data_format},
            timeout=self.timeout,
        )
        if resp.status_code >= 400:
            raise BrightDataError(
                f"Snapshot download failed ({resp.status_code}): {resp.text[:500]}"
            )
        if data_format == "json":
            # Bright Data returns either a JSON array or newline-delimited JSON.
            text = resp.text.strip()
            try:
                return resp.json()
            except ValueError:
                import json

                return [json.loads(line) for line in text.splitlines() if line.strip()]
        return resp.text

    def collect_dataset(
        self,
        inputs: list[dict[str, Any]],
        poll_interval: int = 10,
        max_wait: int = 1800,
        extra_params: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """One-shot: trigger, wait, and return the rows."""
        snapshot_id = self.trigger_dataset(inputs, extra_params=extra_params)
        self.wait_for_snapshot(
            snapshot_id, poll_interval=poll_interval, max_wait=max_wait
        )
        rows = self.fetch_snapshot(snapshot_id, data_format="json")
        if isinstance(rows, dict):
            rows = [rows]
        return rows
