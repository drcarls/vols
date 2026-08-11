"""Live resolution trigger for the geopolitical sleeve — makes ENTRY odds-driven, not hindsight.

The backtest ladder (docs/geo-sleeve-backtest-ladder.md) validated the *exit* discipline given a
correct entry. This module supplies the entry, live: the sleeve stays flat while an event is only
being *anticipated*, and turns on when the decision-odds cross an activation threshold — the
*resolution* channel (the strong one). It then decays out over a weeks-scale half-life (the validated
exit), and deactivates if the odds collapse back (the resolution reversed).

Concretely it sets a per-event ``resolution_decay`` in [0, 1] that multiplies the ``edge`` in
``build_geo_signal`` (default 1.0 when absent, so nothing changes for callers that don't use it):

    watching (prob < activate)         -> resolution_decay = 0.0   (no tilt: anticipation, not resolution)
    just resolved (prob >= activate)   -> resolution_decay = 1.0   (full tilt at the catalyst)
    settling (weeks since activation)  -> resolution_decay = 0.5**(weeks/half_life)   (rotate out)
    reversed (prob < deactivate)       -> cleared, back to watching

State (when each event first resolved) persists as JSON so the decay clock survives across runs. It
needs ``today`` passed in (the caller supplies date.today()) — no wall-clock is read here.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path


def load_state(path: str | None) -> dict:
    """Load {event: {activated_on: 'YYYY-MM-DD', peak_prob: float}} from JSON. Missing -> {}."""
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    try:
        obj = json.loads(p.read_text())
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def save_state(path: str | None, state: dict) -> None:
    if not path:
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2, sort_keys=True))


def _weeks(a_iso: str, b_iso: str) -> float:
    return (date.fromisoformat(b_iso) - date.fromisoformat(a_iso)).days / 7.0


def apply_resolution_trigger(
    events: list[dict],
    state: dict,
    today: str,
    *,
    activate_at: float = 0.5,
    deactivate_at: float = 0.35,
    half_life_weeks: float = 8.0,
) -> tuple[list[dict], dict]:
    """Gate + decay each event by its live decision-odds. Returns (events_with_decay, new_state).

    - ``activate_at``: odds at/above this mark the resolution -> the tilt turns on (decay 1.0).
    - ``deactivate_at``: odds below this after activation -> the resolution reversed -> clear (flat).
    - ``half_life_weeks``: post-activation decay (the exit); weeks are measured from ``activated_on``.

    Structural themes with no ``kalshi_ticker`` (e.g. REARM) have no live odds to resolve on; they are
    left untouched (``resolution_decay`` defaults to 1.0 downstream) so they behave as before.
    """
    state = {k: dict(v) for k, v in (state or {}).items()}
    out: list[dict] = []
    for ev in events or []:
        ev = dict(ev)
        name = ev.get("event")
        # No live market -> not a resolvable event; leave it to its static behaviour.
        if not ev.get("kalshi_ticker"):
            out.append(ev)
            continue
        prob = float(ev.get("prob", 0.0))
        st = state.get(name)
        if st is None:
            if prob >= activate_at:
                st = {"activated_on": today, "peak_prob": prob}
                state[name] = st
        else:
            if prob < deactivate_at:
                state.pop(name, None)
                st = None
            else:
                st["peak_prob"] = max(float(st.get("peak_prob", 0.0)), prob)
        if st is None:
            ev["resolution_decay"] = 0.0
            ev["resolution_state"] = "watching"
        else:
            wk = max(0.0, _weeks(st["activated_on"], today))
            ev["resolution_decay"] = 0.5 ** (wk / float(half_life_weeks)) if half_life_weeks > 0 else 1.0
            ev["resolution_state"] = "active"
        out.append(ev)
    return out, state
