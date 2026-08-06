"""Download the HFS Interest_rates workbook (no API key).

Historical Financial Statistics (Center for Financial Stability) publishes its
workbooks as plain downloads. This fetches the ``Interest_rates.xlsb`` once;
parsing is in :mod:`hfs_rates.parse`.

The raw HFS workbook is **not redistributed** in this repo (HFS restricts
database redistribution); the tool downloads it on demand and emits only the
derived weekly spread series. ``curl`` is tried first (reliable through a
TLS-reintercepting proxy) with a ``urllib`` fallback.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import urllib.request
from typing import Optional

HFS_INTEREST_RATES_URL = (
    "https://www.centerforfinancialstability.org/hfs/Interest_rates.xlsb"
)
_UA = "hfs_rates/0.1 (research)"


def _curl(url: str, dest: str, timeout: float) -> bool:
    curl = shutil.which("curl")
    if not curl:
        return False
    r = subprocess.run(
        [curl, "-sS", "-L", "--http1.1", "--max-time", str(int(timeout)),
         "-A", _UA, url, "-o", dest],
        capture_output=True, timeout=timeout + 15,
    )
    return r.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 100_000


def _urllib(url: str, dest: str, timeout: float) -> bool:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    with open(dest, "wb") as fh:
        fh.write(data)
    return os.path.getsize(dest) > 100_000


def download_workbook(
    dest: str = "Interest_rates.xlsb",
    *,
    url: str = HFS_INTEREST_RATES_URL,
    timeout: float = 180.0,
) -> str:
    """Download the workbook to ``dest`` and return the path.

    Skips the download if ``dest`` already exists and is non-trivial in size, so
    reruns are cheap. Raises if neither transport yields a plausible file.
    """
    if os.path.exists(dest) and os.path.getsize(dest) > 100_000:
        return dest
    for transport in (_curl, _urllib):
        try:
            if transport(url, dest, timeout):
                return dest
        except Exception:
            continue
    raise RuntimeError(f"could not download HFS workbook from {url}")
