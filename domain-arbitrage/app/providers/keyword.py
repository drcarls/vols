"""Keyword / commercial-intent providers.

Shipped implementations:

  * ``NullKeywordProvider``  - the default. Reports everything MISSING.
  * ``CsvKeywordProvider``   - reads a keyword export you supply (Google Ads
    Keyword Planner, Semrush, Ahrefs, DataForSEO all export this shape).

Deliberately absent: any provider that *invents* search volume. A stub that
returns "a plausible CPC" would poison every downstream number while looking
like data. If you have no keyword source, the pipeline runs with commercial
intent MISSING and says so.
"""

from __future__ import annotations

import csv
from pathlib import Path

from app.providers.base import KeywordMetrics, KeywordProvider
from app.provenance import (Sourced, derived, missing, observed,
                            utcnow)

NO_SOURCE_NOTE = (
    "No keyword data source configured. Set KEYWORD_PROVIDER=csv and "
    "KEYWORD_CSV_PATH, or implement a live provider (Google Ads, Semrush, "
    "Ahrefs, DataForSEO)."
)


class NullKeywordProvider(KeywordProvider):
    """Always MISSING. This is the honest default, not a placeholder."""

    name = "keyword.null"

    @property
    def available(self) -> bool:
        return False

    def fetch(self, domain: str, words: list[str]) -> KeywordMetrics:
        return KeywordMetrics.all_missing(self.name, NO_SOURCE_NOTE)


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace("$", "").replace(",", "").replace("%", "")
    if not text or text.lower() in {"na", "n/a", "none", "null", "-"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _commercial_intent(cpc: float | None, competition: float | None,
                       volume: float | None) -> Sourced[float]:
    """0..100 composite. DERIVED - only computed from values we actually have.

    CPC is the dominant term because advertisers paying real money per click is
    the strongest available evidence that a keyword has commercial value.
    Returns MISSING when neither CPC nor competition is known; volume alone says
    nothing about intent.
    """
    if cpc is None and competition is None:
        return missing("keyword.derived", "no CPC or competition data")
    parts: list[float] = []
    weights: list[float] = []
    if cpc is not None:
        # $20+ CPC saturates the scale. Log-shaped: the step from $0.50 to $3
        # means far more than $30 to $35.
        import math
        parts.append(min(100.0, math.log10(1.0 + max(0.0, cpc)) / math.log10(21.0) * 100.0))
        weights.append(0.7)
    if competition is not None:
        parts.append(min(100.0, max(0.0, competition) * 100.0))
        weights.append(0.3)
    score = sum(p * w for p, w in zip(parts, weights)) / sum(weights)
    confidence = 0.8 if (cpc is not None and competition is not None) else 0.5
    return derived(round(score, 2), "keyword.derived", confidence=confidence,
                   note=f"from cpc={cpc}, competition={competition}")


class CsvKeywordProvider(KeywordProvider):
    """Keyword metrics from a CSV you supply.

    Expected columns (case-insensitive, all optional except ``keyword``)::

        keyword,search_volume,cpc,competition,category,geo_specificity,
        intent_type,evidence_url

    Lookup order for a domain: the full second-level string with no separators,
    then the space-joined word list, then the longest single word present.
    Fields absent from the file stay MISSING; they are not back-filled.
    """

    name = "keyword.csv"

    def __init__(self, path: Path | None) -> None:
        self.path = Path(path) if path else None
        self._table: dict[str, dict[str, str]] = {}
        self._loaded = False

    @property
    def available(self) -> bool:
        return bool(self.path and self.path.exists())

    def _load(self) -> None:
        if self._loaded or not self.available:
            self._loaded = True
            return
        assert self.path is not None
        with self.path.open(newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                lower = {(k or "").strip().lower(): (v or "").strip()
                         for k, v in row.items()}
                key = lower.get("keyword", "").strip().lower()
                if key:
                    self._table[key] = lower
        self._loaded = True

    def _lookup(self, domain: str, words: list[str]) -> dict[str, str] | None:
        self._load()
        sld = domain.split(".")[0]
        candidates = [sld.replace("-", ""), " ".join(words), "".join(words)]
        candidates += sorted((w for w in words if len(w) > 3), key=len, reverse=True)
        for cand in candidates:
            hit = self._table.get(cand.strip().lower())
            if hit:
                return hit
        return None

    def fetch(self, domain: str, words: list[str]) -> KeywordMetrics:
        if not self.available:
            return KeywordMetrics.all_missing(
                self.name, f"keyword CSV not found at {self.path}")
        row = self._lookup(domain, words)
        if row is None:
            return KeywordMetrics.all_missing(
                self.name, "no matching keyword row in the supplied file")

        url = row.get("evidence_url") or None
        stamp = utcnow()

        def obs(field: str, cast=_to_float) -> Sourced:
            raw = row.get(field)
            val = cast(raw) if cast else (raw or None)
            if val is None or (isinstance(val, str) and not val):
                return missing(self.name, f"column {field!r} absent or empty")
            s = observed(val, self.name, confidence=0.9, evidence_url=url)
            s.retrieved_at = stamp
            return s

        volume = obs("search_volume")
        cpc = obs("cpc")
        competition = obs("competition")
        category = obs("category", cast=None)
        geo = obs("geo_specificity", cast=None)
        intent = obs("intent_type", cast=None)

        commercial = _commercial_intent(
            None if cpc.is_missing else float(cpc.value),
            None if competition.is_missing else float(competition.value),
            None if volume.is_missing else float(volume.value),
        )

        # Market attractiveness needs both demand and monetisation. If either is
        # unknown we say so rather than scoring on half the picture.
        if volume.is_missing or commercial.is_missing:
            attractiveness: Sourced = missing(
                "keyword.derived", "needs both search volume and commercial intent")
        else:
            import math
            demand = min(100.0, math.log10(1.0 + float(volume.value)) / 5.0 * 100.0)
            attractiveness = derived(
                round(0.5 * demand + 0.5 * float(commercial.value), 2),
                "keyword.derived", confidence=0.6)

        return KeywordMetrics(
            search_volume=volume, cpc_usd=cpc, competition=competition,
            commercial_intent=commercial, category=category,
            geo_specificity=geo, intent_type=intent,
            market_attractiveness=attractiveness)


def build_keyword_provider(kind: str, csv_path: Path | None) -> KeywordProvider:
    if kind == "csv":
        return CsvKeywordProvider(csv_path)
    return NullKeywordProvider()
