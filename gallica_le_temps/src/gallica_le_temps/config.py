"""Run configuration, loaded from YAML.

Everything the pipeline needs is data-driven: the date window, the OCR-quality
floor, which page(s) to read, and a list of *targets*. A target is a named
quantity described by the text anchors that precede its value and a rule for how
many tokens the value spans. No dates or securities are hard-coded in the
package, so any crisis window can be described in a config file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional, Sequence

from .sru import LE_TEMPS_TITLE_ARK


@dataclass(frozen=True)
class TargetSpec:
    """A quantity to extract, located by text anchor."""

    name: str
    anchors: Sequence[str]
    """Text phrases preceding the value, tried in order (OCR spelling variants)."""

    page: int = 1
    max_tokens: int = 1
    skip_tokens: int = 0
    include_anchor: bool = False
    pad_ratio: float = 0.15
    unit: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class RunConfig:
    """A full extraction run."""

    date_start: str  # YYYY-MM-DD
    date_end: str  # YYYY-MM-DD inclusive
    targets: Sequence[TargetSpec]
    title_ark: str = LE_TEMPS_TITLE_ARK
    min_ocr_quality: Optional[float] = 80.0
    output_path: Optional[str] = None
    iiif_size: str = "full"

    def dates(self) -> List[str]:
        """Every calendar date in ``[date_start, date_end]`` as ``YYYY-MM-DD``."""
        start = _parse_date(self.date_start)
        end = _parse_date(self.date_end)
        if end < start:
            raise ValueError("date_end precedes date_start")
        out: List[str] = []
        cur = start
        while cur <= end:
            out.append(cur.isoformat())
            cur += timedelta(days=1)
        return out


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


def _target_from_dict(d: dict) -> TargetSpec:
    anchors = d.get("anchors")
    if isinstance(anchors, str):
        anchors = [anchors]
    if not anchors:
        raise ValueError(f"target {d.get('name')!r} needs at least one anchor")
    return TargetSpec(
        name=d["name"],
        anchors=list(anchors),
        page=int(d.get("page", 1)),
        max_tokens=int(d.get("max_tokens", 1)),
        skip_tokens=int(d.get("skip_tokens", 0)),
        include_anchor=bool(d.get("include_anchor", False)),
        pad_ratio=float(d.get("pad_ratio", 0.15)),
        unit=d.get("unit"),
        notes=d.get("notes"),
    )


def config_from_dict(data: dict) -> RunConfig:
    """Build a :class:`RunConfig` from a plain dict (already-parsed YAML)."""
    targets = [_target_from_dict(t) for t in data.get("targets", [])]
    if not targets:
        raise ValueError("config must define at least one target")
    return RunConfig(
        date_start=str(data["date_start"]),
        date_end=str(data["date_end"]),
        targets=targets,
        title_ark=str(data.get("title_ark", LE_TEMPS_TITLE_ARK)),
        min_ocr_quality=(
            None
            if data.get("min_ocr_quality", 80.0) is None
            else float(data.get("min_ocr_quality", 80.0))
        ),
        output_path=data.get("output_path"),
        iiif_size=str(data.get("iiif_size", "full")),
    )


def load_config(path: str) -> RunConfig:
    """Load a :class:`RunConfig` from a YAML file."""
    import yaml

    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"config at {path} is not a mapping")
    return config_from_dict(data)
