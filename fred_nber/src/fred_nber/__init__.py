"""fred_nber — pull keyless FRED / NBER-Macrohistory sovereign yields and emit the
tidy long ``(date, series, value)`` spread CSV that ``crisis_lag`` consumes.

Unlike ``imm_yale`` (whose Yale backend was down), this path is verified
end-to-end against live open data: FRED serves the NBER Macrohistory series as
CSV with no API key. Coverage is France, Germany and the England-Consol
benchmark; Russia and Austria-Hungary are absent from NBER as bond yields and
still need the IMM.

Pipeline: :mod:`client` (keyless FRED CSV) -> :mod:`spreads` (yield over the
Consol benchmark, in bp; tidy long CSV). :mod:`catalog` maps each power to its
FRED/NBER series.
"""

from __future__ import annotations

from .catalog import Catalog, FredSeries, default_catalog, load_catalog
from .client import YieldSeries, fetch_series, parse_csv
from .spreads import SpreadRow, coverage, to_spread_rows, write_long_csv

__all__ = [
    "Catalog",
    "FredSeries",
    "default_catalog",
    "load_catalog",
    "YieldSeries",
    "fetch_series",
    "parse_csv",
    "SpreadRow",
    "coverage",
    "to_spread_rows",
    "write_long_csv",
]

__version__ = "0.1.0"
