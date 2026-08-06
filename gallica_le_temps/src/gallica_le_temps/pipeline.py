"""Orchestrate: dates -> issues -> pages -> locate -> crop -> (optional) OCR.

The pipeline is deterministic and side-effect-light: it takes an
:class:`~gallica_le_temps.config.RunConfig`, an HTTP client
(:class:`~gallica_le_temps.client.HttpClient`) and an optional
:class:`~gallica_le_temps.extract.Extractor`, and yields one
:class:`ExtractionResult` per (date, target). Callers decide what to do with the
rows (write CSV, load a DataFrame, ...). Injecting the client keeps every step
testable against fixtures.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from typing import Iterable, List, Optional, Sequence

from .alto import alto_url, parse_alto
from .client import HttpClient
from .config import RunConfig, TargetSpec
from .extract import Extractor, first_number
from .iiif import full_size_from_info, info_url, region_crop_url, scale_region
from .locate import locate_value
from .sru import (
    build_issue_query,
    build_sru_params,
    parse_sru_response,
    SRU_ENDPOINT,
)


@dataclass
class ExtractionResult:
    """One located quantity (or a reason it could not be located)."""

    date: str
    target: str
    status: str  # "ok" | "no_issue" | "low_quality" | "not_found" | "no_value"
    ark: Optional[str] = None
    ocr_quality: Optional[float] = None
    page: Optional[int] = None
    anchor_text: Optional[str] = None
    region: Optional[str] = None  # IIIF "x,y,w,h"
    crop_url: Optional[str] = None
    ocr_text: Optional[str] = None
    value: Optional[str] = None  # Decimal rendered as str
    unit: Optional[str] = None
    note: Optional[str] = None


CSV_FIELDS = [
    "date",
    "target",
    "status",
    "ark",
    "ocr_quality",
    "page",
    "anchor_text",
    "region",
    "crop_url",
    "ocr_text",
    "value",
    "unit",
    "note",
]


class Pipeline:
    def __init__(
        self,
        client: HttpClient,
        *,
        extractor: Optional[Extractor] = None,
        sru_endpoint: str = SRU_ENDPOINT,
    ) -> None:
        self._client = client
        self._extractor = extractor
        self._sru_endpoint = sru_endpoint
        # Cache ALTO and info.json per (ark, page) within a run.
        self._alto_cache: dict = {}
        self._info_cache: dict = {}

    # --- individual steps (each independently testable) --------------------

    def find_issue(self, date: str, config: RunConfig):
        """SRU-search the issue for ``date``; return the best IssueRecord or None."""
        query = build_issue_query(
            date,
            title_ark=config.title_ark,
            min_ocr_quality=config.min_ocr_quality,
        )
        params = build_sru_params(query, maximum_records=5)
        xml = self._client.get_text(self._sru_endpoint, params=params)
        records = parse_sru_response(xml)
        if not records:
            return None
        # Prefer the record whose date matches; else the first.
        for rec in records:
            if rec.date == date:
                return rec
        return records[0]

    def _alto_words(self, ark: str, page: int):
        key = (ark, page)
        if key not in self._alto_cache:
            xml = self._client.get_text(alto_url(ark, page))
            self._alto_cache[key] = parse_alto(xml)
        return self._alto_cache[key]

    def _iiif_size(self, ark: str, page: int):
        key = (ark, page)
        if key not in self._info_cache:
            info = self._client.get_json(info_url(ark, page))
            self._info_cache[key] = full_size_from_info(info)
        return self._info_cache[key]

    def extract_target(
        self, date: str, rec, target: TargetSpec, config: RunConfig
    ) -> ExtractionResult:
        """Locate one target on its page and build the crop URL / OCR value."""
        words = self._alto_words(rec.ark, target.page)
        region = locate_value(
            words,
            target.anchors,
            max_tokens=target.max_tokens,
            skip_tokens=target.skip_tokens,
            include_anchor=target.include_anchor,
            pad_ratio=target.pad_ratio,
        )
        if region is None:
            return ExtractionResult(
                date=date,
                target=target.name,
                status="not_found",
                ark=rec.ark,
                ocr_quality=rec.ocr_quality,
                page=target.page,
                unit=target.unit,
                note="no anchor matched on page",
            )

        iiif_w, iiif_h = self._iiif_size(rec.ark, target.page)
        pixel = scale_region(region, iiif_w, iiif_h)
        url = region_crop_url(
            rec.ark, target.page, region, iiif_w, iiif_h, size=config.iiif_size
        )

        ocr_text = None
        value = None
        if self._extractor is not None:
            image = self._client.get_bytes(url)
            ocr_text = self._extractor.extract(image)
            parsed = first_number(ocr_text)
            value = str(parsed) if parsed is not None else None

        return ExtractionResult(
            date=date,
            target=target.name,
            status="ok" if (self._extractor is None or value is not None) else "no_value",
            ark=rec.ark,
            ocr_quality=rec.ocr_quality,
            page=target.page,
            anchor_text=region.text,
            region=pixel.as_iiif(),
            crop_url=url,
            ocr_text=ocr_text,
            value=value,
            unit=target.unit,
        )

    # --- whole-run driver ---------------------------------------------------

    def run(self, config: RunConfig) -> Iterable[ExtractionResult]:
        """Yield one :class:`ExtractionResult` per (date, target)."""
        for date in config.dates():
            rec = self.find_issue(date, config)
            if rec is None:
                for target in config.targets:
                    yield ExtractionResult(
                        date=date,
                        target=target.name,
                        status="no_issue",
                        unit=target.unit,
                        note="no issue matched SRU query (date or ocr-quality filter)",
                    )
                continue
            # Belt-and-suspenders: the SRU query already carries an ocrquality
            # clause, but re-check the per-record quality when Gallica reports it,
            # in case the arkPress+ocrquality combination did not filter.
            if (
                config.min_ocr_quality is not None
                and rec.ocr_quality is not None
                and rec.ocr_quality < config.min_ocr_quality
            ):
                for target in config.targets:
                    yield ExtractionResult(
                        date=date,
                        target=target.name,
                        status="low_quality",
                        ark=rec.ark,
                        ocr_quality=rec.ocr_quality,
                        unit=target.unit,
                        note=(
                            f"ocr quality {rec.ocr_quality:.1f} "
                            f"< floor {config.min_ocr_quality:.1f}"
                        ),
                    )
                continue
            for target in config.targets:
                yield self.extract_target(date, rec, target, config)


def write_csv(rows: Sequence[ExtractionResult], path: str) -> None:
    """Write results to a CSV at ``path``."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: v for k, v in asdict(row).items() if k in CSV_FIELDS})


def collect(rows: Iterable[ExtractionResult]) -> List[ExtractionResult]:
    return list(rows)
