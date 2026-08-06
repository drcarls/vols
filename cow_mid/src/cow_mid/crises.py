"""Map the pre-1914 crises to specific MID disputes, and emit crisis_lag events.

This is the analytical step: identifying *which* militarized dispute each named
crisis is, so ``crisis_lag`` can take its onset date **objectively from COW**
rather than from a hand-typed guess. Each mapping records the dispute number, the
fiscally-binding series (the power whose spread carries the stress — a choice the
thesis makes, constrained to a plausible actor), and a rationale.

Two honest results fall out of the coding:

* **Morocco 1905 (First Moroccan Crisis) has no great-power MID.** It never
  crossed COW's militarization threshold, so it cannot get an objective onset
  here and is omitted (not silently mapped to a wrong dispute).
* **The Balkans/Austria onset is objectively 1912-11-21** (dispute 21,
  Austria-Hungary vs Russia+Serbia), later than the First Balkan War's opening —
  Austria's *militarized* involvement began with the mobilisation crisis, not the
  war between the Balkan states. Bosnia 1908, Agadir 1911 and July 1914 match the
  hand-coded onsets exactly (a useful validation).

For Bosnia 1908 the binding power (Russia) is *not* a militarized participant in
dispute 30 (Serbia vs Austria-Hungary) — Russia backed down below the threshold.
That mismatch is recorded, not hidden.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .parse import Dispute


@dataclass(frozen=True)
class CrisisMapping:
    name: str
    dispnum: Optional[str]  # None => no great-power MID (documented gap)
    series: str  # crisis_lag series id (fiscally-binding power)
    binding_power: str
    measurable: bool = True
    decision_window_days: Optional[int] = None
    search_days: int = 180
    rationale: str = ""


# The mapping. dispnum values are identified from MID v5 by date + participants.
CRISIS_MAPPINGS: List[CrisisMapping] = [
    CrisisMapping(
        name="Morocco_1905", dispnum=None, series="france",
        binding_power="France (First Moroccan Crisis)",
        rationale="No great-power MID — the 1905 crisis stayed below COW's "
                  "militarization threshold; no objective onset available.",
    ),
    CrisisMapping(
        name="Bosnia_1908", dispnum="30", series="russia",
        binding_power="Russia (backed Serbia; climbed down)",
        search_days=210,
        rationale="MID 30 (1908-10-06, Serbia vs Austria-Hungary, use of force). "
                  "Russia is the binding power but was NOT a militarized "
                  "participant — it backed down below the threshold.",
    ),
    CrisisMapping(
        name="Agadir_1911", dispnum="315", series="germany",
        binding_power="Germany (illiquid)",
        rationale="MID 315 (1911-07-01, Germany vs France+UK, display of force). "
                  "Onset matches the hand-coded Agadir date.",
    ),
    CrisisMapping(
        name="Balkans_1912_13", dispnum="21", series="austria_hungary",
        binding_power="Austria-Hungary (Bilinski)",
        search_days=300,
        rationale="MID 21 (1912-11-21, Austria-Hungary vs Russia+Serbia, display "
                  "of force) — Austria's militarized onset, later than the First "
                  "Balkan War's opening.",
    ),
    CrisisMapping(
        name="July_1914", dispnum="257", series="austria_hungary",
        binding_power="Austria, underwritten from Berlin",
        measurable=False, decision_window_days=5,
        rationale="MID 257 (1914-07-23, war; Central Powers vs Entente). Onset "
                  "matches the Austrian ultimatum; peak censored (bourses closed).",
    ),
]


def build_events(disputes: Dict[str, Dispute]) -> List[dict]:
    """Turn the mappings + resolved disputes into crisis_lag event dicts.

    Only crises with a dispnum that resolves to a dated dispute get an event;
    the rest are skipped (their absence is the finding). Each event's ``onset``
    is COW's objective dispute onset date.
    """
    events: List[dict] = []
    for m in CRISIS_MAPPINGS:
        if m.dispnum is None:
            continue
        disp = disputes.get(m.dispnum)
        if disp is None or disp.onset is None:
            continue
        ev = {
            "name": m.name,
            "onset": disp.onset.isoformat(),
            "series": m.series,
            "binding_power": m.binding_power,
            "search_days": m.search_days,
            "notes": (
                f"COW MID {m.dispnum}: {disp.hostlev_label}; "
                f"sideA={disp.names(disp.side_a)} sideB={disp.names(disp.side_b)}. "
                + m.rationale
            ),
        }
        if not m.measurable:
            ev["measurable"] = False
            ev["decision_window_days"] = m.decision_window_days
        events.append(ev)
    return events


def unmapped(disputes: Dict[str, Dispute]) -> List[str]:
    """Names of crises with no usable MID onset (documented gaps)."""
    out = []
    for m in CRISIS_MAPPINGS:
        if m.dispnum is None or m.dispnum not in disputes or disputes[m.dispnum].onset is None:
            out.append(m.name)
    return out
