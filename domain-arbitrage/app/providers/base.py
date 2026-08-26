"""Provider interfaces.

A provider is the only place external data enters the system. Every provider
obeys three rules:

  1. It returns ``Sourced`` values carrying provenance, source, timestamp and
     confidence.
  2. When it cannot answer, it returns ``MISSING``. It never returns a plausible
     default, a zero, or an average.
  3. It declares its own availability, so the pipeline can record *which* data
     sources were live for a given run.

Adding Google Ads / Semrush / Ahrefs / DataForSEO later means implementing
``KeywordProvider`` and registering it - nothing downstream changes.
"""

from __future__ import annotations

import datetime as _dt
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.provenance import Provenance, Sourced, missing, utcnow


@dataclass
class KeywordMetrics:
    """Commercial-intent metrics for a domain's keyword content.

    Every field is a ``Sourced`` so a partially-answered response is
    representable: a provider may know search volume but not CPC.
    """

    search_volume: Sourced[float]
    cpc_usd: Sourced[float]
    competition: Sourced[float]              # 0..1 advertiser competition
    commercial_intent: Sourced[float]        # 0..100
    category: Sourced[str]
    geo_specificity: Sourced[str]            # none | city | region | country
    intent_type: Sourced[str]                # transactional | commercial | informational | navigational
    market_attractiveness: Sourced[float]    # 0..100

    @classmethod
    def all_missing(cls, source: str, note: str) -> "KeywordMetrics":
        return cls(**{f: missing(source, note) for f in cls.__dataclass_fields__})

    def missing_fields(self) -> list[str]:
        return [name for name in self.__dataclass_fields__
                if getattr(self, name).is_missing]

    def as_records(self) -> dict[str, Sourced[Any]]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}


@dataclass
class BuyerCandidateRecord:
    """One candidate end-user buyer.

    INTEGRITY: ``company_name`` and ``company_domain`` must come from a source
    record. Providers may derive ``reason_for_match``, ``match_score`` and
    ``buyer_value_score``; they may never derive the company itself.
    """

    company_name: str
    company_domain: str | None
    reason_for_match: str
    match_type: str
    match_score: float                    # 0..100 - strength of the domain fit
    buyer_value_score: float              # 0..100 - economic weight of the buyer
    provenance: Provenance
    source: str
    evidence_url: str | None = None
    company_size_estimate: str | None = None
    employee_count: int | None = None
    funding_if_known: float | None = None
    funding_currency: str | None = None
    last_funding_date: _dt.datetime | None = None
    industry: str | None = None
    confidence: float = 0.0
    retrieved_at: _dt.datetime = field(default_factory=utcnow)
    llm_rationale: str | None = None


@dataclass
class BuyerSearchResult:
    candidates: list[BuyerCandidateRecord]
    provenance: Provenance
    source: str
    searched: bool
    note: str | None = None

    @property
    def is_missing(self) -> bool:
        """True when buyer depth is UNKNOWN, as opposed to known-to-be-zero.

        This distinction matters enormously: 'we found no buyers' is a finding;
        'we did not look' is not. The scoring layer must not treat them alike.
        """
        return not self.searched or self.provenance is Provenance.MISSING


class Provider(ABC):
    name: str = "provider"

    @property
    @abstractmethod
    def available(self) -> bool:
        """False when credentials or data files are absent."""

    def describe(self) -> dict[str, Any]:
        return {"name": self.name, "available": self.available,
                "class": type(self).__name__}


class KeywordProvider(Provider):
    """Search-volume / CPC / intent enrichment."""

    @abstractmethod
    def fetch(self, domain: str, words: list[str]) -> KeywordMetrics: ...


class BuyerProvider(Provider):
    """End-user buyer discovery."""

    @abstractmethod
    def find_buyers(self, domain: str, sld: str, tld: str, words: list[str],
                    category: str | None = None,
                    limit: int = 50) -> BuyerSearchResult: ...
