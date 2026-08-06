"""Parse the IMM data-table response into monthly yield observations.

⚠️ **Verified boundary.** The Yale query backend returned no populated rows for
any selection during development (``RECON.md``), so the *exact* column order of a
data-bearing response could not be observed live. This parser is therefore
written defensively: it locates the results table, matches columns **by header
text** (not by fixed position), and is exercised by tests against a synthetic
table built from the documented Yale column labels. When the backend serves real
rows, drop one saved response into ``tests/fixtures/`` and the header-matching
approach adapts without code changes; if Yale's labels differ, extend
``COLUMN_ALIASES`` — the one place column names live.

The sentinel string "There are no records matching your selection" is the
backend's empty-result page and is reported as ``status="no_records"`` (an empty
body — a server-side error path we also observed — is ``status="empty"``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Dict, List, Optional

from .lsd import lsd_to_percent, parse_number
from .spread import YieldSeries

NO_RECORDS_MARKERS = (
    "no records matching your selection",
    "did not return any results",
)

# Map a normalised header cell -> a canonical field name. Extend here if Yale's
# labels differ from the form's variable names.
COLUMN_ALIASES: Dict[str, str] = {
    "year": "year",
    "month": "month",
    "yieldinvtlatepricepound": "yield_pound",
    "yieldinvtlatepriceshilling": "yield_shilling",
    "yieldinvtlatepricepence": "yield_pence",
    "yield pound": "yield_pound",
    "yield shilling": "yield_shilling",
    "yield pence": "yield_pence",
    "pricemonthlate": "price_late",
    "late price": "price_late",
    "£": "yield_pound",
    "s": "yield_shilling",
    "d": "yield_pence",
}

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


@dataclass
class ParsedResponse:
    status: str  # "ok" | "no_records" | "empty"
    rows: List[Dict[str, str]] = field(default_factory=list)
    note: Optional[str] = None


class _TableParser(HTMLParser):
    """Collect every HTML table as a list of rows of cell-text."""

    def __init__(self) -> None:
        super().__init__()
        self.tables: List[List[List[str]]] = []
        self._cur_table: Optional[List[List[str]]] = None
        self._cur_row: Optional[List[str]] = None
        self._cell: Optional[List[str]] = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._cur_table = []
        elif tag == "tr" and self._cur_table is not None:
            self._cur_row = []
        elif tag in ("td", "th") and self._cur_row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag == "table" and self._cur_table is not None:
            self.tables.append(self._cur_table)
            self._cur_table = None
        elif tag == "tr" and self._cur_row is not None:
            self._cur_table.append(self._cur_row)
            self._cur_row = None
        elif tag in ("td", "th") and self._cell is not None:
            self._cur_row.append("".join(self._cell).strip())
            self._cell = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def _match_header(cells: List[str]) -> Optional[Dict[int, str]]:
    """If a row looks like a header, return ``{col_index: canonical_field}``."""
    mapping: Dict[int, str] = {}
    for i, c in enumerate(cells):
        key = _norm(c)
        if key in COLUMN_ALIASES:
            mapping[i] = COLUMN_ALIASES[key]
    # Need at least a date anchor and one value column to trust it as a header.
    has_date = "year" in mapping.values() or "month" in mapping.values()
    has_value = any(
        v.startswith("yield") or v == "price_late" for v in mapping.values()
    )
    return mapping if has_date and has_value else None


def parse_response(html: str) -> ParsedResponse:
    """Parse a raw IMM response into canonical rows keyed by column name."""
    if not html or not html.strip():
        return ParsedResponse(status="empty", note="empty body (server-side error path)")
    low = html.lower()
    if any(m in low for m in NO_RECORDS_MARKERS):
        return ParsedResponse(status="no_records", note="backend returned no rows")

    p = _TableParser()
    p.feed(html)
    for table in p.tables:
        header_map: Optional[Dict[int, str]] = None
        rows: List[Dict[str, str]] = []
        for cells in table:
            if header_map is None:
                header_map = _match_header(cells)
                continue
            if not cells:
                continue
            row = {
                field_name: cells[idx]
                for idx, field_name in header_map.items()
                if idx < len(cells)
            }
            if row:
                rows.append(row)
        if header_map and rows:
            return ParsedResponse(status="ok", rows=rows)
    return ParsedResponse(status="empty", note="no results table with known columns")


def _month_num(raw: str) -> Optional[int]:
    t = _norm(raw)
    if t[:3] in _MONTHS:
        return _MONTHS[t[:3]]
    try:
        n = int(float(t))
        return n if 1 <= n <= 12 else None
    except ValueError:
        return None


def rows_to_yields(rows: List[Dict[str, str]]) -> YieldSeries:
    """Reduce parsed rows to ``{"YYYY-MM": yield_percent}``.

    A row needs a year, a month, and at least a pound part of the yield; rows
    missing those are skipped rather than guessed.
    """
    out: YieldSeries = {}
    for r in rows:
        year_raw = r.get("year", "")
        try:
            year = int(float(_norm(year_raw)))
        except ValueError:
            continue
        month = _month_num(r.get("month", ""))
        if month is None:
            continue
        pound = parse_number(r.get("yield_pound"))
        if pound is None:
            continue
        pct = lsd_to_percent(
            pound,
            parse_number(r.get("yield_shilling")),
            parse_number(r.get("yield_pence")),
        )
        if pct is not None:
            out[f"{year:04d}-{month:02d}"] = pct
    return out
