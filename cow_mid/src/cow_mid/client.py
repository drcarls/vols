"""Download the COW MID v5 data bundle (open, no login) and extract MIDA/MIDB.

The Correlates of War project (founded at Michigan, mirrored at ICPSR) publishes
MID v5 as an open zip from its own site — the same data as the ICPSR study, no
account required. This fetches it once and extracts just the two CSVs used here.
``curl`` is tried first (reliable through a TLS-reintercepting proxy) with a
``urllib`` fallback.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import urllib.request
import zipfile
from typing import Tuple

MID5_URL = "https://correlatesofwar.org/wp-content/uploads/MID-5-Data-and-Supporting-Materials.zip"
MIDA_NAME = "MIDA 5.0.csv"
MIDB_NAME = "MIDB 5.0.csv"
_UA = "cow_mid/0.1 (research)"


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


def download_mid5(cache_dir: str = ".", *, timeout: float = 120.0) -> Tuple[str, str]:
    """Ensure MIDA/MIDB CSVs are present in ``cache_dir``; return their paths.

    Skips the network entirely if both CSVs already exist. Otherwise downloads the
    zip and extracts just those two members.
    """
    os.makedirs(cache_dir, exist_ok=True)
    mida = os.path.join(cache_dir, MIDA_NAME)
    midb = os.path.join(cache_dir, MIDB_NAME)
    if os.path.exists(mida) and os.path.exists(midb):
        return mida, midb

    zip_path = os.path.join(cache_dir, "mid5.zip")
    ok = False
    for transport in (_curl, _urllib):
        try:
            if transport(MID5_URL, zip_path, timeout):
                ok = True
                break
        except Exception:
            continue
    if not ok:
        raise RuntimeError(f"could not download MID v5 from {MID5_URL}")

    with zipfile.ZipFile(zip_path) as z:
        for member in (MIDA_NAME, MIDB_NAME):
            z.extract(member, cache_dir)
    return mida, midb
