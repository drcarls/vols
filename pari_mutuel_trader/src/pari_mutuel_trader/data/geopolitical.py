"""Geopolitical mispricing sleeve — signal construction.

Turns prediction-market decision-odds (Kalshi/Polymarket P) into a per-symbol equity tilt, using
the "instrument problem" logic: the risk of a conflict lives in a specific *exposed instrument*
(oil for Iran/Hormuz, freight for the Red Sea, semis for Taiwan, ...), and the tradeable edge is the
gap between the decision-odds and the disruption premium the instrument is *already* pricing.

For each live event e with market probability ``prob_e`` and an implied premium ``premium_e`` already
in its instrument (both in [0, 1]), the per-name signal is::

    geo_signal[symbol] = sum_e  (prob_e - premium_e) * exposure[e][symbol]

``exposure`` is *signed*: a name that BENEFITS from the disruption (an oil major when Hormuz is
threatened) carries a positive weight; a name that is HURT by it (a chip designer if Taiwan is
threatened) carries a negative weight. So a positive edge (odds richer than the premium) tilts the
book toward beneficiaries and away from victims; a negative edge (the premium is already rich — a
fading scare) does the reverse. The sleeve does not try to time the war; it tilts toward names
carrying an odds-vs-premium gap the rest of the book is not pricing.

Data: ``prob_e`` comes from the Kalshi/prediction-market feed; ``premium_e`` from the instrument's
implied vol / skew / term-structure (e.g. OVX for oil). With no events supplied the sleeve is
neutral (all-zero), exactly like the news/macro agents when their column is absent.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

# Signed exposure map: event -> {ticker: weight}. Positive = benefits from the disruption,
# negative = hurt by it. A sensible, liquid default; override via config for a live book.
DEFAULT_EXPOSURE_MAP: dict[str, dict[str, float]] = {
    # Iran / Strait of Hormuz -> oil supply shock: energy & tankers up, oil-importers down.
    "IRAN_HORMUZ": {
        "XOM": 1.0, "CVX": 1.0, "COP": 1.0, "OXY": 1.0, "EOG": 0.8, "SLB": 0.8,
        "FRO": 1.2, "STNG": 1.2, "INSW": 1.0, "DHT": 1.0,
        "DAL": -0.6, "LUV": -0.6, "UAL": -0.6,
    },
    # Red Sea / Bab-el-Mandeb -> shipping/freight up (reroute), some oil.
    "RED_SEA": {"ZIM": 1.2, "MATX": 1.0, "XOM": 0.4, "CVX": 0.3},
    # Taiwan -> semiconductor supply disrupted: chip names DOWN (un-priceable tail; trim only).
    "TAIWAN": {"NVDA": -1.0, "AMD": -1.0, "AVGO": -0.8, "TSM": -1.2, "ASML": -0.8, "QCOM": -0.6, "MU": -0.8},
    # China rare-earth / critical-mineral squeeze -> Western miners/processors up.
    "RARE_EARTH": {"MP": 1.5, "ALB": 0.6, "UEC": 0.6},
    # Rearmament (Europe/global defense spend) -> defense primes up.
    "REARM": {"LMT": 1.0, "RTX": 1.0, "NOC": 1.0, "GD": 0.8, "LHX": 0.8, "HII": 0.6},
    # Venezuela / Guyana (oil + specific E&P exposure).
    "VENEZUELA": {"XOM": 0.6, "CVX": 0.5},

    # --- Beyond geopolitics: Kalshi prices the anticipation channel for many events. Each maps to an
    # exposed instrument. Keep only those with a real instrument on a tradeable horizon (see
    # docs/mining-kalshi-for-instruments.md); drop the instrument-less (Sports, Pope) and the
    # un-priceable (Mars-by-2050, supervolcano). ---

    # MACRO (Kalshi Economics: Fed funds, CPI, GDP)
    "FED_HIKE": {"KRE": 1.0, "JPM": 0.6, "TLT": -1.0, "ARKK": -0.8, "GLD": -0.5, "XLU": -0.4},
    "FED_CUT": {"TLT": 1.0, "ARKK": 0.9, "GLD": 0.6, "XLU": 0.4, "KRE": -0.4},
    "CPI_HOT": {"XLE": 0.8, "XOM": 0.6, "FCX": 0.6, "GLD": 0.5, "TLT": -1.0},
    "RECESSION": {"XLP": 0.9, "XLU": 0.7, "GLD": 0.6, "XLY": -0.9, "XLI": -0.8, "HYG": -0.7},

    # POLICY (Kalshi Politics/legislation)
    "TARIFFS": {"GM": -0.7, "NKE": -0.7, "FDX": -0.5, "FXI": -0.8, "EWW": -0.7, "X": 0.6, "NUE": 0.6},
    "DRUG_PRICING": {"PFE": -0.8, "MRK": -0.7, "LLY": -0.6, "CVS": -0.6, "UNH": -0.5},

    # HEALTH (Kalshi FDA approvals) — single-name; example placeholders, set per live market
    "FDA_APPROVAL": {"LLY": 0.6, "NVO": 0.6},

    # CLIMATE/WEATHER (Kalshi hurricanes/quakes) — insurance & energy, NOT the un-priceable long tails
    "MAJOR_HURRICANE": {"ALL": -0.9, "TRV": -0.8, "RNR": 0.6, "XOM": 0.4, "VLO": 0.4},

    # CRYPTO (Kalshi BTC/ETH ranges, ETF) — crypto-exposed equities
    "CRYPTO_RALLY": {"COIN": 1.0, "MSTR": 1.2, "MARA": 1.0},
}


def build_geo_signal(
    symbols: Iterable[str],
    events: list[dict],
    exposure_map: dict[str, dict[str, float]] | None = None,
) -> pd.Series:
    """Per-symbol geopolitical tilt. ``events`` = [{event, prob, premium}, ...] (prob/premium in [0,1]).

    Returns a Series indexed by ``symbols`` (0.0 for names not exposed to any event).
    """
    exposure_map = exposure_map or DEFAULT_EXPOSURE_MAP
    symbols = list(symbols)
    sig = pd.Series(0.0, index=symbols, dtype=float)
    for ev in events or []:
        name = ev.get("event")
        exposure = exposure_map.get(name)
        if not exposure:
            continue
        edge = float(ev.get("prob", 0.0)) - float(ev.get("premium", 0.0))  # odds minus what's priced
        if edge == 0.0:
            continue
        for ticker, weight in exposure.items():
            if ticker in sig.index:
                sig[ticker] += edge * float(weight)
    return sig


def attach_geo_signal(
    features_df: pd.DataFrame,
    events: list[dict],
    exposure_map: dict[str, dict[str, float]] | None = None,
) -> pd.DataFrame:
    """Attach a ``geo_signal`` column (per-symbol tilt broadcast across dates) to a features frame.

    v1 applies the *current* event set cross-sectionally. For a historical backtest, supply a dated
    events table and attach per-date; a static current-event tilt is the live/paper-run default.
    """
    out = features_df.copy()
    syms = out.index.get_level_values("symbol").unique()
    sig = build_geo_signal(syms, events, exposure_map)
    out["geo_signal"] = out.index.get_level_values("symbol").map(sig).astype(float)
    out["geo_signal"] = out["geo_signal"].fillna(0.0)
    return out


def load_events(path: str | None) -> list[dict]:
    """Load a list of live events from YAML/JSON: [{event, prob, premium, kalshi_ticker?}, ...].

    Missing file -> []. This does NOT fetch Kalshi; use ``resolve_events`` for that.
    """
    if not path:
        return []
    p = Path(path)
    if not p.exists():
        return []
    try:
        import yaml  # pyyaml is already a dependency (see config.load_yaml)
        data = yaml.safe_load(p.read_text()) or {}
    except Exception:
        import json
        data = json.loads(p.read_text())
    events = data.get("events", data) if isinstance(data, dict) else data
    return events if isinstance(events, list) else []


def resolve_events(path: str | None, *, use_kalshi: bool = True, use_premium_feed: bool = True) -> list[dict]:
    """Load events and populate ``prob`` (Kalshi) and ``premium`` (instrument implied vol).

    ``prob``   : live Kalshi -> local file -> static config.
    ``premium``: instrument implied vol (OVX/MOVE/VIX, normalized) -> static config.
    So ``edge = prob - premium`` computes hands-free. Degrades gracefully with no network/keys.
    """
    events = load_events(path)
    if use_kalshi and events:
        try:
            from .kalshi import enrich_events
            events = enrich_events(events)
        except Exception:
            pass
    if use_premium_feed and events:
        try:
            from .premium import resolve_premiums
            events = resolve_premiums(events)
        except Exception:
            pass
    return events
