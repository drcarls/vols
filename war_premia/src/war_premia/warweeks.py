"""War-week coding and crisis windows, transcribed from Carls (2005), Appendix
Table 1, plus the July-1914 extension coded by the paper's own conservative rule
(only events directly about the crisis).

Dates are the historical event dates; :func:`nearest_week` maps each to the
Saturday-dated Neal-Weidenmeier observation week. Windows reproduce the sample
periods stated in the paper (First Moroccan's is inferred to ~62 obs — the paper
gives the count, not the endpoints — and is flagged).
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set

D = datetime.date


@dataclass(frozen=True)
class Crisis:
    key: str
    label: str
    window: "tuple[datetime.date, datetime.date]"
    war_events: List[datetime.date]
    stated_n: Optional[int] = None
    note: str = ""


CRISES: List[Crisis] = [
    Crisis(
        "morocco1", "First Moroccan Crisis",
        (D(1905, 1, 7), D(1906, 3, 31)),          # inferred to ~62 obs
        [D(1904, 4, 8), D(1904, 10, 7), D(1904, 11, 1), D(1905, 2, 21),
         D(1905, 3, 31), D(1905, 6, 5), D(1905, 6, 15), D(1905, 6, 22),
         D(1905, 7, 1), D(1905, 12, 30), D(1906, 1, 3), D(1906, 3, 31)],
        stated_n=62, note="window inferred (paper gives n=62, not endpoints)",
    ),
    Crisis(
        "bosnia", "Bosnian Crisis",
        (D(1908, 6, 6), D(1909, 6, 5)),           # stated
        [D(1908, 9, 16), D(1908, 10, 6), D(1908, 10, 28), D(1909, 3, 2),
         D(1909, 3, 10), D(1909, 3, 22), D(1909, 3, 31)],
        stated_n=51,
    ),
    Crisis(
        "morocco2", "Second Moroccan Crisis",
        (D(1911, 5, 6), D(1911, 9, 30)),          # stated
        [D(1911, 5, 21), D(1911, 6, 21), D(1911, 7, 1), D(1911, 7, 21),
         D(1911, 7, 24), D(1911, 8, 8)],          # Nov 4 treaty is outside the window
        stated_n=22,
    ),
    Crisis(
        "balkans", "Balkan Wars",
        (D(1912, 9, 1), D(1913, 8, 6)),           # stated
        [D(1912, 10, 8), D(1912, 12, 3), D(1912, 12, 16), D(1913, 1, 23),
         D(1913, 5, 30), D(1913, 6, 29), D(1913, 7, 31)],
    ),
    Crisis(
        "full", "Full sub-sample",
        (D(1904, 3, 4), D(1913, 6, 13)),          # stated, 485 obs
        # union of all four crises' war weeks
        [],  # filled below
        stated_n=485,
    ),
]

# The full-sample crisis uses every crisis's war weeks.
_full = next(c for c in CRISES if c.key == "full")
_allweeks = sorted({d for c in CRISES if c.key != "full" for d in c.war_events})
CRISES = [c for c in CRISES if c.key != "full"] + [
    Crisis(_full.key, _full.label, _full.window, _allweeks, _full.stated_n, _full.note)
]

# --- July-1914 extension (coded by the paper's conservative, crisis-only rule) ---
JULY_1914_EVENTS: List[datetime.date] = [
    D(1914, 6, 28),   # Assassination of Archduke Franz Ferdinand at Sarajevo
    D(1914, 7, 23),   # Austria-Hungary's ultimatum to Serbia
    D(1914, 7, 25),   # Serbia's reply; Austria breaks relations, partial mobilisation
    D(1914, 7, 28),   # Austria-Hungary declares war on Serbia
    D(1914, 7, 30),   # Russian general mobilisation
    D(1914, 7, 31),   # German ultimatums; London Stock Exchange closes
    D(1914, 8, 1),    # Germany declares war on Russia; general mobilisations
    D(1914, 8, 3),    # Germany declares war on France
    D(1914, 8, 4),    # Germany invades Belgium; Britain declares war on Germany
]

# Windows for the 1914 run on each asset class (short rates end 1914-06-27).
JULY_1914_SHORT_WINDOW = (D(1913, 6, 14), D(1914, 6, 27))   # extends the paper by a year
JULY_1914_BONDS_WINDOW = (D(1913, 6, 14), D(1914, 10, 7))   # spans the crisis


def nearest_week(event: datetime.date, obs_dates: Sequence[datetime.date]) -> Optional[datetime.date]:
    """Map an event to the closest observation week (min |day difference|)."""
    if not obs_dates:
        return None
    return min(obs_dates, key=lambda d: abs((d - event).days))


def war_mask(
    obs_dates: Sequence[datetime.date],
    events: Sequence[datetime.date],
    *,
    max_gap_days: int = 6,
) -> List[bool]:
    """Boolean per observation date: is it the nearest week to some war event?"""
    war_weeks: Set[datetime.date] = set()
    for e in events:
        nw = nearest_week(e, obs_dates)
        if nw is not None and abs((nw - e).days) <= max_gap_days:
            war_weeks.add(nw)
    return [d in war_weeks for d in obs_dates]


def get_crisis(key: str) -> Crisis:
    for c in CRISES:
        if c.key == key:
            return c
    raise KeyError(key)
