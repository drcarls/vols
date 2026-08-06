"""Reshape extraction results into a canonical daily time series.

:class:`~gallica_le_temps.pipeline.ExtractionResult` rows are one-per
``(date, target)`` and carry provenance. For downstream analysis we want a tidy
series that concatenates cleanly with other sources (e.g. a weekly first source),
in two shapes:

* **long / tidy** — one row per ``(date, series)`` with a ``source`` column and
  full provenance. This is the canonical join target: stack sources with a plain
  concat, keyed on ``(date, series)``.
* **wide** — one row per date, one column per series. Built on a *complete daily
  date spine* so every calendar day in the window is present; days with no
  quotation (markets closed, missing scan) stay as explicit empty cells rather
  than vanishing, which keeps it a genuine daily series ready to align with a
  weekly one.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Sequence

from .pipeline import ExtractionResult

DEFAULT_SOURCE = "le_temps"


@dataclass
class SeriesPoint:
    """One observation in the tidy long series."""

    date: str
    series: str
    value: Optional[str]  # Decimal rendered as str, or None when not read
    unit: Optional[str]
    source: str
    status: str
    ark: Optional[str] = None
    page: Optional[int] = None
    ocr_quality: Optional[float] = None
    region: Optional[str] = None
    crop_url: Optional[str] = None


LONG_FIELDS = [
    "date",
    "series",
    "value",
    "unit",
    "source",
    "status",
    "ark",
    "page",
    "ocr_quality",
    "region",
    "crop_url",
]


def to_long(
    results: Sequence[ExtractionResult], *, source: str = DEFAULT_SOURCE
) -> List[SeriesPoint]:
    """Convert extraction results into tidy :class:`SeriesPoint` rows."""
    points: List[SeriesPoint] = []
    for r in results:
        points.append(
            SeriesPoint(
                date=r.date,
                series=r.target,
                value=r.value,
                unit=r.unit,
                source=source,
                status=r.status,
                ark=r.ark,
                page=r.page,
                ocr_quality=r.ocr_quality,
                region=r.region,
                crop_url=r.crop_url,
            )
        )
    return points


def write_long_csv(
    results: Sequence[ExtractionResult],
    path: str,
    *,
    source: str = DEFAULT_SOURCE,
) -> int:
    """Write the tidy long series to ``path``; return the row count."""
    points = to_long(results, source=source)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=LONG_FIELDS)
        writer.writeheader()
        for p in points:
            writer.writerow(asdict(p))
    return len(points)


def series_order(results: Sequence[ExtractionResult]) -> List[str]:
    """Series names in first-seen order (stable column order for the wide form)."""
    seen: List[str] = []
    for r in results:
        if r.target not in seen:
            seen.append(r.target)
    return seen


def to_wide(
    results: Sequence[ExtractionResult],
    *,
    dates: Optional[Sequence[str]] = None,
    series: Optional[Sequence[str]] = None,
) -> "tuple[List[str], List[dict]]":
    """Pivot results to one row per date, one column per series.

    ``dates`` supplies the daily spine: when given, a row is emitted for *every*
    date in it (empty cells where there is no value), yielding a gap-free daily
    index. When omitted, only dates present in ``results`` appear. ``value`` is
    used as the cell; a series with no parsed value that day is left blank.
    """
    cols = list(series) if series is not None else series_order(results)

    # Index parsed values by (date, series). Last write wins on the rare dupe.
    cell: Dict[tuple, str] = {}
    result_dates: List[str] = []
    for r in results:
        if r.date not in result_dates:
            result_dates.append(r.date)
        if r.value is not None:
            cell[(r.date, r.target)] = r.value

    spine = list(dates) if dates is not None else result_dates
    fieldnames = ["date"] + cols
    rows: List[dict] = []
    for d in spine:
        row = {"date": d}
        for s in cols:
            row[s] = cell.get((d, s), "")
        rows.append(row)
    return fieldnames, rows


def write_wide_csv(
    results: Sequence[ExtractionResult],
    path: str,
    *,
    dates: Optional[Sequence[str]] = None,
    series: Optional[Sequence[str]] = None,
) -> int:
    """Write the wide daily series to ``path``; return the number of date rows."""
    fieldnames, rows = to_wide(results, dates=dates, series=series)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)
