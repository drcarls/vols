"""cow_mid — objective crisis onset dates and hostility levels for crisis_lag,
from the Correlates of War Militarized Interstate Dispute (MID v5) data.

crisis_lag's event onsets were hand-coded; this replaces the guesswork with COW's
externally-coded dispute onset date and 1–5 hostility level. Pipeline:
:mod:`client` (download MID v5) -> :mod:`parse` (join MIDA+MIDB) -> :mod:`crises`
(map each crisis to its dispute; emit the events spec).
"""

from __future__ import annotations

from .client import download_mid5
from .crises import CRISIS_MAPPINGS, CrisisMapping, build_events, unmapped
from .parse import Dispute, join_disputes, load_disputes
from .capability import capability_series, parse_nmc
from .warrisk import GREAT_POWERS, RiskPoint, war_risk_series

__all__ = [
    "download_mid5",
    "CRISIS_MAPPINGS", "CrisisMapping", "build_events", "unmapped",
    "Dispute", "join_disputes", "load_disputes",
    "GREAT_POWERS", "RiskPoint", "war_risk_series",
    "capability_series", "parse_nmc",
]

__version__ = "0.1.0"
