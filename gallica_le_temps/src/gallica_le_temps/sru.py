"""Gallica SRU search (CQL) for Le Temps issues.

Le Temps is a periodical; each daily issue is a separate Gallica document with
its own ARK. The ``arkPress`` index maps a periodical's title-notice ARK plus a
date to that day's issue::

    arkPress all "cb34431794k_date19140728"

where ``cb34431794k`` is the ARK of the Le Temps title notice
(``ark:/12148/cb34431794k``). The ``ocrquality`` index (0-100) lets us keep
only good scans; Gallica also returns a per-record OCR-quality figure in the
record's ``extraRecordData`` which we parse for post-filtering.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as _date
from typing import List, Optional
from xml.etree import ElementTree as ET

from .xmlutil import find_local, iter_local, local_name

SRU_ENDPOINT = "https://gallica.bnf.fr/SRU"

# ARK of the Le Temps (1861-1942) title notice, sans the ``ark:/12148/`` prefix.
LE_TEMPS_TITLE_ARK = "cb34431794k"


def format_ocr_threshold(value: float) -> str:
    """Format an OCR-quality threshold the way the SRU ``ocrquality`` index wants.

    The index compares against a zero-padded ``NNN.NN`` string, so ``80`` -> and
    ``"080.00"``.
    """
    if not 0 <= value <= 100:
        raise ValueError(f"ocr quality must be in [0, 100], got {value!r}")
    return f"{value:06.2f}"


def build_issue_query(
    date: str,
    *,
    title_ark: str = LE_TEMPS_TITLE_ARK,
    min_ocr_quality: Optional[float] = None,
) -> str:
    """Build a CQL query for the issue of ``title_ark`` published on ``date``.

    ``date`` is ``YYYY-MM-DD``. When ``min_ocr_quality`` is given, an
    ``ocrquality`` clause is added so the server pre-filters low-quality scans.
    """
    try:
        parsed = _date.fromisoformat(date)
    except ValueError as exc:
        raise ValueError(f"date must be YYYY-MM-DD, got {date!r}") from exc
    compact = parsed.strftime("%Y%m%d")
    clause = f'arkPress all "{title_ark}_date{compact}"'
    if min_ocr_quality is not None:
        clause += f' and ocrquality > "{format_ocr_threshold(min_ocr_quality)}"'
    return clause


def build_sru_params(query: str, *, maximum_records: int = 5, start: int = 1) -> dict:
    """Assemble the SRU ``searchRetrieve`` query parameters."""
    return {
        "operation": "searchRetrieve",
        "version": "1.2",
        "query": query,
        "maximumRecords": str(maximum_records),
        "startRecord": str(start),
    }


@dataclass(frozen=True)
class IssueRecord:
    """One issue returned by an SRU search."""

    ark: str
    """The document ARK id, e.g. ``bpt6k239abc`` (no ``ark:/12148/`` prefix)."""

    date: Optional[str]
    """The ``dc:date`` of the issue, if present (``YYYY-MM-DD``)."""

    title: Optional[str]
    ocr_quality: Optional[float]
    """Mean OCR quality (0-100) parsed from ``extraRecordData`` if present."""

    identifier_url: Optional[str] = None


def _ark_id_from_identifier(identifier: str) -> Optional[str]:
    """Pull the ``bpt6k...`` id out of a Gallica ARK URL or ARK string."""
    if not identifier:
        return None
    marker = "ark:/12148/"
    if marker in identifier:
        tail = identifier.split(marker, 1)[1]
    else:
        tail = identifier.rstrip("/").rsplit("/", 1)[-1]
    # Strip any trailing path (e.g. ``.item``, ``/f1``) and query.
    tail = tail.split("/", 1)[0].split("?", 1)[0].split(".", 1)[0]
    return tail or None


def _parse_ocr_quality(record: ET.Element) -> Optional[float]:
    """Best-effort read of the per-record OCR quality from ``extraRecordData``.

    Gallica exposes this under tags such as ``ocrQuality`` / ``nqamoyen``; we try
    a few and take the first that parses as a number in [0, 100].
    """
    for tag in ("ocrQuality", "nqamoyen", "ocrquality", "score_ocr"):
        el = find_local(record, tag)
        if el is not None and el.text:
            try:
                val = float(el.text.strip().replace(",", "."))
            except ValueError:
                continue
            if 0 <= val <= 100:
                return val
    return None


def parse_sru_response(xml_text: str) -> List[IssueRecord]:
    """Parse an SRU ``searchRetrieveResponse`` into :class:`IssueRecord` rows."""
    root = ET.fromstring(xml_text)
    records: List[IssueRecord] = []
    for record in iter_local(root, "record"):
        # Dublin-Core payload lives under recordData.
        identifier_url: Optional[str] = None
        date: Optional[str] = None
        title: Optional[str] = None
        for child in record.iter():
            name = local_name(child.tag)
            text = (child.text or "").strip()
            if not text:
                continue
            if name == "identifier" and identifier_url is None:
                # Prefer an ARK-bearing identifier if several are present.
                if "ark:/12148/" in text or identifier_url is None:
                    identifier_url = text
            elif name == "date" and date is None:
                date = text
            elif name == "title" and title is None:
                title = text
        ark = _ark_id_from_identifier(identifier_url or "")
        if ark is None:
            continue
        records.append(
            IssueRecord(
                ark=ark,
                date=date,
                title=title,
                ocr_quality=_parse_ocr_quality(record),
                identifier_url=identifier_url,
            )
        )
    return records


def sru_number_of_records(xml_text: str) -> int:
    """Return the SRU ``numberOfRecords`` count (0 if absent)."""
    root = ET.fromstring(xml_text)
    el = find_local(root, "numberOfRecords")
    if el is not None and el.text and el.text.strip().isdigit():
        return int(el.text.strip())
    return 0
