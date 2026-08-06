"""Crisis event specification for the falsification test.

The book's central testable claim: in each pre-war crisis the lag from *crisis
onset* to *peak financial stress* — read off the sovereign spread series — was
consistently ~6–10 weeks, while the July 1914 decision window was ~5 days. If so,
the financial brake did not fail in 1914; it was given a fifth of the time it
needed.

A :class:`CrisisEvent` ties a crisis to (a) its onset date, (b) which power's
spread carries the stress (the fiscally-binding power that chapter), and (c) the
windows used to define a baseline and to search for the peak. July 1914 is
special: the market closed, so its peak is right-censored and *not* measured —
what matters is its decision-window length against the comparators' lags.

The defaults below are PROVISIONAL. The onset dates and the binding-power→series
mapping are exactly the "event dates and specification" to reconcile against the
original thesis dataset; every field is overridable via YAML
(:func:`load_events`).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional


@dataclass(frozen=True)
class CrisisEvent:
    name: str
    onset: str  # YYYY-MM-DD — crisis onset (t0)
    series: str  # series id in the data whose spread carries the stress
    binding_power: str  # human label for the fiscally-binding power
    measurable: bool = True  # False when the peak is censored (market closed)
    decision_window_days: Optional[int] = None  # e.g. July 1914 ~5
    # Baseline window: [onset - baseline_start_days, onset - baseline_end_days].
    baseline_start_days: int = 120
    baseline_end_days: int = 14
    # Peak search window: [onset, onset + search_days].
    search_days: int = 180
    notes: Optional[str] = None

    def onset_date(self) -> date:
        return date.fromisoformat(self.onset)


# Provisional Belle Époque comparator set + the July 1914 test point.
# Onset dates are the escalation events; the series mapping names the power under
# fiscal pressure in that crisis. All are overridable — see load_events().
DEFAULT_EVENTS: List[CrisisEvent] = [
    CrisisEvent(
        name="Morocco_1905",
        onset="1905-03-31",  # Kaiser at Tangier
        series="russia",
        binding_power="France / Russia",
        notes="Ch. I: consent missing; Russian bonds collapsing in French portfolios.",
    ),
    CrisisEvent(
        name="Bosnia_1908",
        onset="1908-10-06",  # annexation proclaimed
        series="russia",
        binding_power="Russia (Kokovtsov)",
        search_days=210,  # peak stress ran into the Mar 1909 German note
        notes="Ch. II: Russia had neither money nor a short war.",
    ),
    CrisisEvent(
        name="Agadir_1911",
        onset="1911-07-01",  # Panther arrives at Agadir
        series="germany",
        binding_power="Germany (illiquid)",
        notes="Ch. III archetype: Berlin bourse/discount peak early Sep ~10 wk.",
    ),
    CrisisEvent(
        name="Balkans_1912_13",
        onset="1912-10-08",  # First Balkan War opens
        series="austria_hungary",
        binding_power="Austria-Hungary (Bilinski)",
        search_days=300,  # the crisis ran through two winters; peak in 1913
        notes="Ch. IV: money on the day, spent already on a war not fought.",
    ),
    CrisisEvent(
        name="July_1914",
        onset="1914-07-23",  # Austrian ultimatum to Serbia
        series="austria_hungary",
        binding_power="Austria, underwritten from Berlin",
        measurable=False,  # bourses closed late July -> peak is censored
        decision_window_days=5,
        notes="Test point: window ~5 days; Austria's gap underwritten a fortnight prior.",
    ),
]


def event_from_dict(d: dict) -> CrisisEvent:
    return CrisisEvent(
        name=d["name"],
        onset=str(d["onset"]),
        series=d["series"],
        binding_power=d.get("binding_power", d["series"]),
        measurable=bool(d.get("measurable", True)),
        decision_window_days=d.get("decision_window_days"),
        baseline_start_days=int(d.get("baseline_start_days", 120)),
        baseline_end_days=int(d.get("baseline_end_days", 14)),
        search_days=int(d.get("search_days", 180)),
        notes=d.get("notes"),
    )


def load_events(path: str) -> List[CrisisEvent]:
    """Load crisis events from a YAML file (a list under key ``events``)."""
    import yaml

    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    items = data["events"] if isinstance(data, dict) else data
    return [event_from_dict(d) for d in items]
