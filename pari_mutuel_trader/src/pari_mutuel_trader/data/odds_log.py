"""Append-only logger of live decision-odds + premium, so a dated panel accumulates over time.

The resolution trigger (``data/resolution.py``) can't be backtested today because Kalshi odds history
for these bespoke events is sparse. This closes that gap *going forward*: every ``build-features`` run
appends one row per event to a CSV, so after a few months you hold a genuine dated ``(prob, premium)``
panel — the exact input a real trigger backtest needs. Stdlib only (csv), matching the repo style.

Columns: ``date, event, kalshi_ticker, prob, prob_source, premium, premium_source,
resolution_state, resolution_decay``. Append is idempotent per ``(date, event)`` so re-running on the
same day does not duplicate rows.
"""
from __future__ import annotations

import csv
from pathlib import Path

FIELDS = [
    "date", "event", "kalshi_ticker", "prob", "prob_source",
    "premium", "premium_source", "resolution_state", "resolution_decay",
]


def _existing_keys(path: Path) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    if not path.exists():
        return keys
    try:
        with path.open(newline="") as f:
            for row in csv.DictReader(f):
                keys.add((row.get("date", ""), row.get("event", "")))
    except Exception:
        pass
    return keys


def append_odds_snapshot(events: list[dict], path: str | None, today: str) -> int:
    """Append one row per event for ``today``; skip events already logged that day. Returns rows written."""
    if not path or not events or not today:
        return 0
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    seen = _existing_keys(p)
    rows = []
    for ev in events:
        name = ev.get("event")
        if name is None or (today, name) in seen:
            continue
        rows.append({
            "date": today,
            "event": name,
            "kalshi_ticker": ev.get("kalshi_ticker", ""),
            "prob": ev.get("prob", ""),
            "prob_source": ev.get("prob_source", "static"),
            "premium": ev.get("premium", ""),
            "premium_source": ev.get("premium_source", "static"),
            "resolution_state": ev.get("resolution_state", ""),
            "resolution_decay": ev.get("resolution_decay", ""),
        })
    if not rows:
        return 0
    write_header = not p.exists()
    with p.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if write_header:
            w.writeheader()
        w.writerows(rows)
    return len(rows)


def load_odds_panel(path: str | None):
    """Load the accumulated panel as a DataFrame (date parsed, sorted). Missing -> empty frame."""
    import pandas as pd
    if not path or not Path(path).exists():
        return pd.DataFrame(columns=FIELDS)
    df = pd.read_csv(path, parse_dates=["date"])
    return df.sort_values(["date", "event"]).reset_index(drop=True)
