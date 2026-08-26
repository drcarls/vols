"""Provenance primitives.

Every enriched field in this system carries provenance so that any number in the
final ranking can be traced back to how it came to exist. This is the single most
important integrity rule in the codebase:

    Missing information is never converted into invented information.

A field that could not be sourced is stored with ``Provenance.MISSING`` and a
``None`` value. Downstream consumers must branch on that rather than substituting
a default silently.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Generic, Optional, TypeVar


class Provenance(str, Enum):
    """How a value came to exist."""

    OBSERVED = "OBSERVED"
    """Directly read from an external source of record (a listing, an API, a
    recorded sale). The value is a fact about the world."""

    DERIVED = "DERIVED"
    """Computed deterministically from OBSERVED inputs by code in this repo.
    Reproducible: same inputs -> same output, no model, no randomness."""

    ESTIMATED = "ESTIMATED"
    """Produced by a heuristic or statistical model in this repo. Carries real
    uncertainty. In V0 these are hand-set priors that have NOT been calibrated
    against outcomes."""

    LLM_INFERRED = "LLM_INFERRED"
    """Produced by a language model. Used only for semantic judgement, never for
    arithmetic, parsing, or scoring rules."""

    FIXTURE = "FIXTURE"
    """Came from a synthetic example file shipped for demos and tests. NEVER
    real. Gated behind ``allow_fixture_data`` and always surfaced as a warning."""

    MISSING = "MISSING"
    """Could not be sourced. The value is None. Do not substitute a default."""


def utcnow() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


T = TypeVar("T")


@dataclass
class Sourced(Generic[T]):
    """A value plus everything needed to audit it.

    ``confidence`` is 0..1 and expresses how much weight downstream models should
    give the value. MISSING values always have confidence 0.0.
    """

    value: Optional[T]
    provenance: Provenance
    source: str
    retrieved_at: _dt.datetime = field(default_factory=utcnow)
    confidence: float = 0.0
    evidence_url: Optional[str] = None
    note: Optional[str] = None

    @property
    def is_missing(self) -> bool:
        return self.provenance is Provenance.MISSING or self.value is None

    def or_else(self, fallback: T) -> T:
        """Explicit, greppable fallback.

        Callers must use this rather than ``x.value or default`` so that every
        place a missing value influences a number is visible in the source.
        """
        return fallback if self.is_missing else self.value  # type: ignore[return-value]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["provenance"] = self.provenance.value
        d["retrieved_at"] = self.retrieved_at.isoformat()
        return d


def missing(source: str, note: str | None = None) -> Sourced[Any]:
    """Construct an explicitly-missing value."""
    return Sourced(value=None, provenance=Provenance.MISSING, source=source,
                   confidence=0.0, note=note)


def observed(value: T, source: str, *, confidence: float = 1.0,
             evidence_url: str | None = None, note: str | None = None) -> Sourced[T]:
    return Sourced(value, Provenance.OBSERVED, source, confidence=confidence,
                   evidence_url=evidence_url, note=note)


def derived(value: T, source: str, *, confidence: float = 1.0,
            note: str | None = None) -> Sourced[T]:
    return Sourced(value, Provenance.DERIVED, source, confidence=confidence, note=note)


def estimated(value: T, source: str, *, confidence: float,
              note: str | None = None) -> Sourced[T]:
    return Sourced(value, Provenance.ESTIMATED, source, confidence=confidence, note=note)


def llm_inferred(value: T, source: str, *, confidence: float,
                 note: str | None = None) -> Sourced[T]:
    return Sourced(value, Provenance.LLM_INFERRED, source, confidence=confidence, note=note)


def fixture(value: T, source: str, *, confidence: float = 0.5,
            evidence_url: str | None = None, note: str | None = None) -> Sourced[T]:
    return Sourced(value, Provenance.FIXTURE, source, confidence=confidence,
                   evidence_url=evidence_url,
                   note=note or "SYNTHETIC EXAMPLE DATA - not a real observation")
