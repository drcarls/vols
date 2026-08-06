"""Keyless client for FRED time series (the NBER Macrohistory mirror).

FRED serves any series as CSV from a plain URL with **no API key**:

    https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES_ID>

That is the whole interface used here. We pull the pre-1914 sovereign-yield
series from the NBER Macrohistory database (Chapter 13, Interest Rates), which
FRED hosts under ``…NNBR`` ids. ``urllib`` honours the environment's
``HTTPS_PROXY`` and CA bundle, so no extra configuration is needed.
"""

from __future__ import annotations

import csv
import io
import shutil
import subprocess
import time
import urllib.request
from typing import Dict, Optional

# A monthly yield series: {"YYYY-MM": percent}.
YieldSeries = Dict[str, float]

FREDGRAPH_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={id}"

# FRED renders a missing observation as a single ".".
_MISSING = {".", "", "n/a", "NA"}


def _fetch_urllib(url: str, timeout: float) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "fred_nber/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def _fetch_curl(url: str, timeout: float) -> str:
    # Fallback for TLS-reintercepting proxies where urllib stalls but curl,
    # which honours the HTTPS_PROXY/CA env directly, succeeds.
    curl = shutil.which("curl")
    if not curl:
        raise RuntimeError("curl not available for fallback")
    out = subprocess.run(
        [curl, "-sS", "-L", "--max-time", str(int(timeout)), url],
        capture_output=True, text=True, timeout=timeout + 10,
    )
    if out.returncode != 0:
        raise RuntimeError(f"curl failed ({out.returncode}): {out.stderr.strip()[:200]}")
    return out.stdout


def fetch_csv(series_id: str, *, timeout: float = 30.0, retries: int = 3) -> str:
    """Return the raw CSV text for one FRED series id (keyless).

    Tries the system ``curl`` first (reliable through TLS-reintercepting proxies)
    and falls back to ``urllib``; both honour the environment's proxy/CA config.
    Non-empty CSV is required — a body that is blank or lacks a comma is treated
    as a failed fetch and retried.
    """
    url = FREDGRAPH_CSV.format(id=series_id)
    last: Optional[Exception] = None
    transports = (_fetch_curl, _fetch_urllib) if shutil.which("curl") else (_fetch_urllib,)
    for attempt in range(retries):
        for fetch in transports:
            try:
                text = fetch(url, timeout)
                if text and "," in text:
                    return text
                last = RuntimeError("empty/short body")
            except Exception as e:  # try the other transport, then back off
                last = e
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"FRED fetch failed for {series_id}: {last}")


def parse_csv(text: str) -> YieldSeries:
    """Parse FRED CSV text into ``{"YYYY-MM": percent}``.

    FRED's first column is the observation date (``YYYY-MM-DD``) and the second
    the value; a "." value is a documented gap and is dropped, never imputed.
    """
    out: YieldSeries = {}
    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)  # observation_date,<ID>
    for row in reader:
        if len(row) < 2:
            continue
        date, raw = row[0].strip(), row[1].strip()
        if raw in _MISSING or len(date) < 7:
            continue
        try:
            out[date[:7]] = float(raw)
        except ValueError:
            continue
    return out


def fetch_series(series_id: str, **kw) -> YieldSeries:
    """Fetch and parse one FRED series into a monthly :data:`YieldSeries`."""
    return parse_csv(fetch_csv(series_id, **kw))
