"""Instrument-premium feed for the geopolitical / prediction-market sleeve.

Populates each event's ``premium`` — the disruption already priced in its exposed instrument —
from the instrument's implied volatility, so ``edge = prob - premium`` computes hands-free.

Each event maps to a vol gauge and a [floor, ceiling] regime band; the premium is the fraction of
that crisis range currently implied::

    premium = clip((vol - floor) / (ceiling - floor), 0, 1)

- Oil events (Iran/Hormuz, Red Sea, Venezuela) -> **OVX** (crude implied vol).
- Rate/macro events (Fed, CPI) -> **MOVE** (bond vol).
- Equity/systemic events (Taiwan, tariffs, recession, crypto, hurricanes) -> **VIX**.
- Events with no clean vol proxy (rare earths, rearm, FDA) keep their static config ``premium``.

Rough by construction — a "how much of the instrument's crisis range is priced now" proxy, tunable
via the floor/ceiling bands. Live vol -> static config, degrading gracefully with no network. Stdlib
only (urllib), matching the repo style.
"""
from __future__ import annotations

import json
import os
import urllib.request

# event -> (yahoo vol symbol, floor, ceiling)
VOL_SOURCES: dict[str, tuple[str, float, float]] = {
    "IRAN_HORMUZ": ("^OVX", 25.0, 100.0),
    "RED_SEA": ("^OVX", 25.0, 100.0),
    "VENEZUELA": ("^OVX", 25.0, 100.0),
    "FED_HIKE": ("^MOVE", 70.0, 200.0),
    "FED_CUT": ("^MOVE", 70.0, 200.0),
    "CPI_HOT": ("^MOVE", 70.0, 200.0),
    "RECESSION": ("^VIX", 12.0, 50.0),
    "TAIWAN": ("^VIX", 12.0, 60.0),
    "TARIFFS": ("^VIX", 12.0, 50.0),
    "DRUG_PRICING": ("^VIX", 12.0, 50.0),
    "MAJOR_HURRICANE": ("^VIX", 12.0, 50.0),
    "CRYPTO_RALLY": ("^VIX", 12.0, 50.0),
    # RARE_EARTH, REARM, FDA_APPROVAL: no clean listed vol proxy -> keep static config premium.
}


def fetch_vol(symbol: str, timeout: float = 6.0) -> float | None:
    """Latest close of a vol index (e.g. ^OVX/^VIX/^MOVE) via the public chart API. None on failure."""
    sym = symbol.replace("^", "%5E")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        vals = [c for c in closes if c is not None]
        return float(vals[-1]) if vals else None
    except Exception:
        return None


def normalized_premium(vol: float | None, floor: float, ceiling: float) -> float | None:
    """Fraction of the [floor, ceiling] crisis range currently implied, clipped to [0, 1]."""
    if vol is None or ceiling <= floor:
        return None
    return max(0.0, min(1.0, (vol - floor) / (ceiling - floor)))


def resolve_premiums(events: list[dict], *, vol_sources: dict | None = None,
                     use_live: bool = True) -> list[dict]:
    """Set each event's ``premium`` from its instrument's implied vol; fall back to static config."""
    if os.getenv("PREMIUM_FEED", "1") == "0":
        use_live = False
    vol_sources = vol_sources or VOL_SOURCES
    cache: dict[str, float | None] = {}
    out: list[dict] = []
    for ev in events or []:
        ev = dict(ev)
        src = vol_sources.get(ev.get("event"))
        if use_live and src:
            sym, floor, ceiling = src
            if sym not in cache:
                cache[sym] = fetch_vol(sym)
            prem = normalized_premium(cache[sym], floor, ceiling)
            if prem is not None:
                ev["premium"] = prem
                ev["premium_source"] = f"vol:{sym}"
        out.append(ev)
    return out
