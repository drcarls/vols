"""imm_yale — pull sovereign yields from the Yale ICF *Investor's Monthly Manual*
and emit the tidy long ``(date, series, value)`` spread CSV that ``crisis_lag``
consumes.

Pipeline: :mod:`client` (query the IMM form) -> :mod:`parse` (read the £-s-d
yield table) -> :mod:`spread` (yield over the UK-Consol benchmark, in bp) ->
:mod:`series` (tidy long CSV). :mod:`config` holds the provisional securities
catalogue mapping each power to its sovereign issue.

See ``RECON.md`` for the reverse-engineered interface and the state of the live
backend at the time of writing.
"""

from __future__ import annotations

from .config import Catalogue, Security, default_catalogue, load_catalogue
from .lsd import cells_to_percent, lsd_to_percent
from .parse import ParsedResponse, parse_response, rows_to_yields
from .series import SeriesPoint, spreads_to_points, write_long_csv
from .spread import SpreadPoint, to_spreads

__all__ = [
    "Catalogue",
    "Security",
    "default_catalogue",
    "load_catalogue",
    "lsd_to_percent",
    "cells_to_percent",
    "ParsedResponse",
    "parse_response",
    "rows_to_yields",
    "SpreadPoint",
    "to_spreads",
    "SeriesPoint",
    "spreads_to_points",
    "write_long_csv",
]

__version__ = "0.1.0"
