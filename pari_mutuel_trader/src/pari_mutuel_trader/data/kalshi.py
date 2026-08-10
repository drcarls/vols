"""Kalshi / prediction-market probability ingest for the geopolitical sleeve.

Populates each event's ``prob`` (the decision-odds) from Kalshi, with graceful fallback. Priority:
  1. **live** — GET the Kalshi market by ticker (best-effort; optional auth via env);
  2. **local** — a file your existing Kalshi pipeline writes (ticker -> prob), CSV or JSON;
  3. **static** — the ``prob`` already in the event config.

So the sleeve keeps working with no network and no keys (it uses the static config), and upgrades to
live odds when a feed is available. Stdlib only (urllib), matching the repo's no-extra-deps style.

Env (all optional):
  KALSHI_API_BASE   default https://api.elections.kalshi.com/trade-api/v2
  KALSHI_API_KEY    bearer token, if your access uses one (best-effort header)
  KALSHI_PROBS_PATH local file of {ticker: prob} your pipeline produces (CSV `ticker,prob` or JSON)
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

DEFAULT_BASE = "https://api.elections.kalshi.com/trade-api/v2"


def implied_prob_from_market(market: dict) -> float | None:
    """Implied YES probability (0..1) from a Kalshi market dict: last_price (cents) or bid/ask mid."""
    if not isinstance(market, dict):
        return None
    lp = market.get("last_price")
    if isinstance(lp, (int, float)) and lp > 0:
        return float(lp) / 100.0
    bid, ask = market.get("yes_bid"), market.get("yes_ask")
    if isinstance(bid, (int, float)) and isinstance(ask, (int, float)) and (bid or ask):
        return (float(bid) + float(ask)) / 200.0
    return None


def fetch_market_prob(ticker: str, base: str | None = None, api_key: str | None = None,
                      timeout: float = 6.0) -> float | None:
    """Best-effort live fetch of one market's implied probability. Returns None on any failure."""
    base = (base or os.getenv("KALSHI_API_BASE") or DEFAULT_BASE).rstrip("/")
    api_key = api_key or os.getenv("KALSHI_API_KEY")
    url = f"{base}/markets/{ticker}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        market = data.get("market", data) if isinstance(data, dict) else {}
        return implied_prob_from_market(market)
    except Exception:
        return None


def load_local_probs(path: str | None = None) -> dict[str, float]:
    """Load {ticker: prob} from a local file your Kalshi pipeline writes (CSV `ticker,prob` or JSON)."""
    path = path or os.getenv("KALSHI_PROBS_PATH")
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    try:
        text = p.read_text()
        if p.suffix.lower() == ".json":
            obj = json.loads(text)
            return {str(k): float(v) for k, v in obj.items()}
        out: dict[str, float] = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.lower().startswith("ticker"):
                continue
            parts = line.replace("\t", ",").split(",")
            if len(parts) >= 2:
                try:
                    out[parts[0].strip()] = float(parts[1])
                except ValueError:
                    pass
        return out
    except Exception:
        return {}


def list_events(category: str | None = None, *, base: str | None = None, api_key: str | None = None,
                max_events: int = 1200, timeout: float = 8.0) -> list[dict]:
    """Discover what Kalshi prices: [{event_ticker, title, category}, ...], optionally by category.

    A discovery engine for *more things to price* — enumerate Kalshi's universe, then filter to the
    markets that map to a real exposed instrument on a tradeable horizon (see the exposure map and
    docs/mining-kalshi-for-instruments.md). Best-effort; returns what it has on any failure.
    """
    base = (base or os.getenv("KALSHI_API_BASE") or DEFAULT_BASE).rstrip("/")
    api_key = api_key or os.getenv("KALSHI_API_KEY")
    out: list[dict] = []
    cursor = ""
    try:
        while len(out) < max_events:
            url = f"{base}/events?limit=200&with_nested_markets=false" + (f"&cursor={cursor}" if cursor else "")
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            if api_key:
                req.add_header("Authorization", f"Bearer {api_key}")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8", "replace"))
            evs = data.get("events", [])
            for e in evs:
                if category and (e.get("category") or "").lower() != category.lower():
                    continue
                out.append({"event_ticker": e.get("event_ticker"), "title": e.get("title"),
                            "category": e.get("category")})
            cursor = data.get("cursor", "")
            if not cursor or not evs:
                break
    except Exception:
        return out
    return out


def enrich_events(events: list[dict], *, base: str | None = None, api_key: str | None = None,
                  local_path: str | None = None, use_live: bool = True) -> list[dict]:
    """Set each event's ``prob`` from Kalshi. Priority: live -> local file -> static config.

    An event opts in by carrying a ``kalshi_ticker``; events without one keep their static ``prob``.
    Probabilities are normalised to [0, 1] (a value > 1 is treated as a percentage).
    """
    local = load_local_probs(local_path)
    out: list[dict] = []
    for ev in events or []:
        ev = dict(ev)
        ticker = ev.get("kalshi_ticker")
        if ticker:
            p, src = None, None
            if use_live:
                p = fetch_market_prob(ticker, base, api_key)
                if p is not None:
                    src = "kalshi_live"
            if p is None and ticker in local:
                p, src = local[ticker], "kalshi_local"
            if p is not None:
                ev["prob"] = p / 100.0 if p > 1.0 else float(p)
                ev["prob_source"] = src
        out.append(ev)
    return out
