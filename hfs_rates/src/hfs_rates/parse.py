"""Read the HFS *Interest rates* workbook into weekly money-market series.

Source: Historical Financial Statistics (Center for Financial Stability), the
``Interest_rates.xlsb`` workbook, sheet ``Market rates--daily``. For the pre-1914
European centres that sheet actually carries **weekly** observations (~756 points
1900–1914) of the open-market (private discount) rate — the money-market stress
measure that tightens when short funding gets scarce.

The sheet is a metadata header block (rows labelled Country / Category / Series /
… in column D) followed by data rows whose column D holds a Gregorian date
``YYYY.MM.DD`` and whose country columns hold the rate. Columns are matched **by
(country, series text)**, not by fixed position, so the reader survives column
reordering in future HFS releases.

The grid→series transform is a pure function (:func:`grid_to_series`) so it is
unit-tested without a workbook; :func:`read_market_rates` only adds the xlsb read.
"""

from __future__ import annotations

import datetime
from typing import Dict, List, Optional, Sequence

RateSeries = Dict[datetime.date, float]

# Column D (index 3) label of each header row we care about.
_COUNTRY_LABEL = "Country"
_SERIES_LABEL = "Series"
_DATE_COL = 3  # column D carries the Gregorian date on data rows


def parse_gregorian(cell) -> Optional[datetime.date]:
    """Parse an HFS ``YYYY.MM.DD`` date cell; ``None`` if it isn't one."""
    if not isinstance(cell, str):
        return None
    parts = cell.split(".")
    if len(parts) != 3:
        return None
    try:
        return datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError:
        return None


def _header_row(grid: Sequence[Sequence], label: str) -> Optional[int]:
    for i, row in enumerate(grid[:20]):
        if len(row) > _DATE_COL and row[_DATE_COL] == label:
            return i
    return None


def find_column(
    grid: Sequence[Sequence], country: str, series_substr: str
) -> Optional[int]:
    """Index of the column whose Country == ``country`` and whose Series text
    contains ``series_substr`` (case-insensitive). ``None`` if not found."""
    crow = _header_row(grid, _COUNTRY_LABEL)
    srow = _header_row(grid, _SERIES_LABEL)
    if crow is None or srow is None:
        return None
    countries, series = grid[crow], grid[srow]
    want = series_substr.lower()
    for j in range(_DATE_COL + 1, len(countries)):
        c = countries[j]
        s = series[j] if j < len(series) else None
        if isinstance(c, str) and c.strip() == country and isinstance(s, str) and want in s.lower():
            return j
    return None


def grid_to_series(
    grid: Sequence[Sequence],
    country: str,
    series_substr: str,
    *,
    start_year: int = 1900,
    end_year: int = 1914,
) -> RateSeries:
    """Extract ``{date: rate}`` for one (country, series) column within a year
    range. Non-numeric / undated rows are skipped, never imputed."""
    col = find_column(grid, country, series_substr)
    if col is None:
        return {}
    out: RateSeries = {}
    for row in grid:
        if len(row) <= col:
            continue
        d = parse_gregorian(row[_DATE_COL] if len(row) > _DATE_COL else None)
        if d is None or not (start_year <= d.year <= end_year):
            continue
        v = row[col]
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            out[d] = float(v)
    return out


def read_grid(path: str, sheet: str = "Market rates--daily") -> List[List]:
    """Read a whole xlsb sheet into a list-of-rows grid (needs ``pyxlsb``)."""
    from pyxlsb import open_workbook

    with open_workbook(path) as wb:
        with wb.get_sheet(sheet) as sh:
            return [[c.v for c in row] for row in sh.rows()]
