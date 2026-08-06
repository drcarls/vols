"""Load the Neal-Weidenmeier Gold Standard Database short-term rates, correctly.

The workbook stores dates across the 1900 boundary in **three segments** (a
classic pre-1900 Excel workaround, since Excel can't hold positive serials before
1900): 1870–mid-1912 shifted **+100 years** (so they read as 1970–2012),
mid-1912→end-1913 stored as **true** dates, and 1914 shifted **+100** again
(reading as 2014). :func:`true_date` undoes it with a rule that is unambiguous for
this file: a raw year ≥ 1970 is a shifted date (−100 years); anything else is
already true.

Decoded, the short-term sheet is continuous **weekly 1870-01-01 → 1914-06-27** —
the eve of Sarajevo (28 June 1914). Note this is the *paper's* variable, and it
ends **before** the July-1914 war weeks; the long-term bond file reaches
1914-10-07 and does span them.

Reads with ``xlrd`` (the workbook is legacy ``.xls``). The header block names each
column by city and rate type (Bank / Open Mkt / 3 mo. Trade); this exposes them as
tidy ``(date, series, value)`` rows so the data feeds the same tooling as the
other legs.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

SHIFT_YEARS = 100
SHIFT_THRESHOLD_YEAR = 1970  # raw years >= this are +100-shifted


def true_date(raw: datetime.date) -> datetime.date:
    """Undo the segmented +100-year storage. Raw year >= 1970 => subtract 100."""
    if raw.year >= SHIFT_THRESHOLD_YEAR:
        try:
            return raw.replace(year=raw.year - SHIFT_YEARS)
        except ValueError:  # 29 Feb in a non-leap century target
            return raw.replace(year=raw.year - SHIFT_YEARS, day=28)
    return raw


@dataclass(frozen=True)
class Observation:
    date: datetime.date
    city: str
    rate_type: str
    value: float


def _slug(city: str, rate_type: str) -> str:
    c = city.strip().lower().replace(" ", "_").replace("'", "").replace(".", "")
    r = rate_type.strip().lower()
    if "open" in r:
        r = "openmkt"
    elif "3 mo" in r or "trade" in r:
        r = "trade3mo"
    elif "bank" in r:
        r = "bank"
    else:
        r = r.replace(" ", "_") or "rate"
    return f"{c}_{r}"


def load_short_rates(path: str) -> List[Observation]:
    """Parse ``stinterestrates.xls`` into tidy observations with true dates.

    The header spans two rows (city on one, rate type on the next); data begins at
    the first row whose first cell is a date. Blank / non-numeric cells are
    skipped, never imputed.
    """
    import xlrd

    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_name(wb.sheet_names()[0])

    # Locate the two header rows: the 'Date' label sits in column 0 of the
    # rate-type row; the city row is the one above it.
    date_row = None
    for r in range(min(10, sh.nrows)):
        if str(sh.cell_value(r, 0)).strip().lower() == "date":
            date_row = r
            break
    if date_row is None:
        raise ValueError("could not find the 'Date' header row")
    city_row = date_row - 1

    # Forward-fill city names across merged/blank header cells.
    cities: List[str] = []
    last_city = ""
    for c in range(sh.ncols):
        v = str(sh.cell_value(city_row, c)).strip()
        if v:
            last_city = v
        cities.append(last_city)
    rate_types = [str(sh.cell_value(date_row, c)).strip() for c in range(sh.ncols)]

    out: List[Observation] = []
    for r in range(date_row + 1, sh.nrows):
        dc = sh.cell(r, 0)
        if dc.ctype != xlrd.XL_CELL_DATE:
            continue
        d = true_date(xlrd.xldate.xldate_as_datetime(dc.value, wb.datemode).date())
        for c in range(1, sh.ncols):
            cell = sh.cell(r, c)
            if cell.ctype != xlrd.XL_CELL_NUMBER:
                continue
            city = cities[c]
            if not city:
                continue
            out.append(Observation(d, city, rate_types[c], float(cell.value)))
    return out


def to_series_map(obs: List[Observation]) -> Dict[str, List[Tuple[datetime.date, float]]]:
    """Group observations into ``{city_ratetype: [(date, value), ...]}`` (sorted)."""
    m: Dict[str, List[Tuple[datetime.date, float]]] = {}
    for o in obs:
        m.setdefault(_slug(o.city, o.rate_type), []).append((o.date, o.value))
    for k in m:
        m[k].sort()
    return m


def span(obs: List[Observation]) -> Optional[Tuple[datetime.date, datetime.date]]:
    if not obs:
        return None
    ds = [o.date for o in obs]
    return min(ds), max(ds)
