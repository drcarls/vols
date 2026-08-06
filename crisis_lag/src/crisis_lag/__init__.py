"""crisis_lag — the falsification test for *The Preconditions*.

Measures the lag from crisis onset to peak financial stress in the sovereign
spread series for the pre-1914 crises, and contrasts it with the July 1914
decision window. Source-agnostic: it consumes the tidy ``(date, series, value)``
long form emitted by ``gallica_le_temps.series``, so monthly IMM spreads and
daily Le Temps quotations feed the same instrument.

    from crisis_lag import DEFAULT_EVENTS, load_long_csv, measure_all, adjudicate
    series = load_long_csv("spreads_long.csv")
    results = measure_all(series, DEFAULT_EVENTS)
    verdict = adjudicate(results)
"""

from .events import CrisisEvent, DEFAULT_EVENTS, load_events
from .lag import LagResult, measure_all, measure_lag
from .report import Verdict, adjudicate, format_table, format_verdict
from .series import load_long_csv, rows_to_series
from .seasonal import deseasonalize, seasonal_index
from .stress import Baseline, baseline_for, stress_series

__all__ = [
    "seasonal_index",
    "deseasonalize",
    "CrisisEvent",
    "DEFAULT_EVENTS",
    "load_events",
    "LagResult",
    "measure_all",
    "measure_lag",
    "Verdict",
    "adjudicate",
    "format_table",
    "format_verdict",
    "load_long_csv",
    "rows_to_series",
    "Baseline",
    "baseline_for",
    "stress_series",
]

__version__ = "0.1.0"
