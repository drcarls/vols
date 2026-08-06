"""hfs_rates — weekly pre-1914 money-market rates from Historical Financial
Statistics (Center for Financial Stability), spread over London, as the tidy
``(date, series, value)`` CSV crisis_lag consumes.

This is the **weekly** leg of the falsification test — finer than the monthly
fred_nber sovereign spreads. Coverage: Austria, France, Germany and the UK
benchmark, weekly 1900–1914 (Russia sparse). value = a power's open-market rate
minus London's, in bp, which differences out most of money markets' common
autumn seasonality (see README).

Pipeline: :mod:`client` (download the HFS workbook) -> :mod:`parse` (weekly
open-market rates) -> :mod:`spreads` (spread over London -> tidy CSV).
:mod:`catalog` maps each power to its HFS column.
"""

from __future__ import annotations

from .catalog import Catalog, RateColumn, default_catalog
from .parse import RateSeries, grid_to_series, parse_gregorian, read_grid
from .spreads import SpreadRow, coverage, to_spread_rows, write_long_csv

__all__ = [
    "Catalog", "RateColumn", "default_catalog",
    "RateSeries", "grid_to_series", "parse_gregorian", "read_grid",
    "SpreadRow", "coverage", "to_spread_rows", "write_long_csv",
]

__version__ = "0.1.0"
