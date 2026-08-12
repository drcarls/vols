from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Company:
    """A candidate prospect for Questa AI.

    In v1 these come from a CSV (Stage 1 input); later a live data.gov /
    SEC EDGAR / state-registry backend can populate the same shape so
    nothing downstream changes.
    """

    name: str
    domain: Optional[str] = None
    naics_code: Optional[str] = None          # US industry code (NAICS)
    employees: Optional[int] = None
    revenue_usd: Optional[float] = None        # annual revenue in USD
    state: Optional[str] = None                # US state (for state-privacy nexus)
    country: str = "US"

    def normalized_name(self) -> str:
        """Company name stripped of legal suffixes, for fuzzy matching."""
        n = self.name.lower().strip()
        for suffix in (
            " incorporated", " inc.", " inc", " llc", " l.l.c.", " llp",
            " l.l.p.", " corp.", " corp", " corporation", " co.", " co",
            " ltd.", " ltd", " pllc", " pc", " p.c.", " lp", " l.p.",
        ):
            if n.endswith(suffix):
                n = n[: -len(suffix)]
        return n.strip(" ,.")


@dataclass
class DataScopeVerdict:
    """Is this a regulated-data organization Questa is built for, and how
    sensitive is the data it handles?"""

    verdict: str                 # in_scope | likely_in_scope | out_of_scope | unknown
    sector: Optional[str]        # matched sector, if any
    data_class: Optional[str]    # PHI | financial | legal_privileged | consumer_pii | None
    regime: Optional[str]        # HIPAA | GLBA | state_privacy | ... | None
    sensitivity: int             # 0..4 (PHI highest)
    reasons: list[str] = field(default_factory=list)


@dataclass
class AiAdoptionSignal:
    """Is the company actively adopting AI right now? Active adoption means
    live data-exposure and budget in motion -- the buy-now trigger."""

    level: str                   # active | emerging | none | unknown
    hiring: Optional[bool] = None        # AI/ML roles open
    public_ai: Optional[bool] = None     # AI mentioned on their own site
    chatbot: Optional[bool] = None       # customer-facing chatbot detected
    hits_considered: int = 0
    findings: list[str] = field(default_factory=list)


@dataclass
class Person:
    name: str
    title: str
    profile_url: Optional[str] = None
    role_tier: str = "generic"   # leader | generic


@dataclass
class GovernanceSignal:
    """Is there a publicly visible owner of privacy / AI governance? Its
    ABSENCE, while AI is being adopted, is the direct Questa opening."""

    status: str                  # governed | none_found | uncertain
    confidence: float            # 0..1 confidence in the reported status
    people: list[Person] = field(default_factory=list)
    verify_recommended: bool = True
    query: Optional[str] = None
    hits_considered: int = 0


@dataclass
class Finding:
    """One observable buying signal, enriched with its business/compliance
    context.

    Collectors emit a bare (code, evidence); the context map turns it into a
    full Finding with severity, the US regulation it maps to, the Questa
    product that addresses it, and a sales talking point.
    """

    company: str
    domain: Optional[str]
    finding_id: str
    title: str
    category: str                 # data | adoption | governance | exposure
    severity: str                 # info | low | medium | high | critical
    severity_score: int           # 1..5, context-adjusted
    evidence: str
    risk: str
    regulation: str               # HIPAA / GLBA / state privacy / EU AI Act ref
    product: str                  # Questa product that addresses it
    remediation: str
    talking_point: str
    source: str = "passive_osint"

    def to_row(self) -> dict:
        return {
            "company_name": self.company,
            "domain": self.domain or "",
            "finding_id": self.finding_id,
            "title": self.title,
            "category": self.category,
            "severity": self.severity,
            "severity_score": self.severity_score,
            "evidence": self.evidence,
            "risk": self.risk,
            "regulation": self.regulation,
            "questa_product": self.product,
            "remediation": self.remediation,
            "talking_point": self.talking_point,
            "source": self.source,
        }


@dataclass
class ProspectReport:
    company: Company
    data_scope: DataScopeVerdict
    adoption: AiAdoptionSignal
    governance: GovernanceSignal
    product: str = ""            # routed Questa product (Blackbox/Developer/Cloud)
    fit_score: float = 0.0
    reasons: list[str] = field(default_factory=list)

    def to_row(self) -> dict:
        """Flatten to a single CSV-friendly record."""
        leader = next((p for p in self.governance.people if p.role_tier == "leader"), None)
        return {
            "name": self.company.name,
            "domain": self.company.domain or "",
            "state": self.company.state or "",
            "employees": self.company.employees if self.company.employees is not None else "",
            "fit_score": round(self.fit_score, 1),
            "questa_product": self.product,
            "data_scope": self.data_scope.verdict,
            "sector": self.data_scope.sector or "",
            "data_class": self.data_scope.data_class or "",
            "regime": self.data_scope.regime or "",
            "ai_adoption": self.adoption.level,
            "governance_status": self.governance.status,
            "governance_confidence": round(self.governance.confidence, 2),
            "governance_owner": leader.name if leader else "",
            "governance_title": leader.title if leader else "",
            "verify_governance": "yes" if self.governance.verify_recommended else "no",
            "reasons": "; ".join(self.reasons),
        }

    def to_dict(self) -> dict:
        return asdict(self)
