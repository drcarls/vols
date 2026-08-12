from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Company:
    """A candidate prospect. In v1 these come from a CSV (Stage 1 input);
    later a live allabolag/Bolagsverket backend can populate the same shape.
    """

    name: str
    domain: Optional[str] = None
    org_number: Optional[str] = None          # Swedish organisationsnummer
    sni_code: Optional[str] = None            # Swedish industry code (SNI)
    employees: Optional[int] = None
    turnover_eur: Optional[float] = None       # annual turnover in EUR
    balance_sheet_eur: Optional[float] = None  # balance-sheet total in EUR
    country: str = "SE"

    def normalized_name(self) -> str:
        """Company name stripped of legal suffixes, for fuzzy matching."""
        n = self.name.lower().strip()
        for suffix in (" ab (publ)", " ab", " hb", " kb", " ekonomisk forening"):
            if n.endswith(suffix):
                n = n[: -len(suffix)]
        return n.strip(" ,.")


@dataclass
class Nis2Verdict:
    verdict: str                 # in_scope | likely_in_scope | out_of_scope | unknown
    sector: Optional[str]        # matched NIS2 sector, if any
    sector_in_scope: bool
    meets_size_threshold: Optional[bool]
    reasons: list[str] = field(default_factory=list)


@dataclass
class EmailSecuritySignal:
    weakness: str                # weak | partial | strong | unknown
    has_spf: Optional[bool] = None
    has_dmarc: Optional[bool] = None
    dmarc_policy: Optional[str] = None   # none | quarantine | reject | None
    findings: list[str] = field(default_factory=list)


@dataclass
class Person:
    name: str
    title: str
    profile_url: Optional[str] = None
    role_tier: str = "generic"   # leader | generic


@dataclass
class CisoSignal:
    status: str                  # visible | none_found | uncertain
    confidence: float            # 0..1 confidence in the reported status
    people: list[Person] = field(default_factory=list)
    verify_recommended: bool = True
    query: Optional[str] = None
    hits_considered: int = 0


@dataclass
class Finding:
    """One observable weakness, enriched with its business/compliance context.

    Collectors emit a bare (code, evidence); the context map turns it into a
    full Finding with severity, the NIS2/ISO obligation it maps to, the
    Cyber Defencely service that addresses it, and a sales talking point.
    """

    company: str
    domain: Optional[str]
    finding_id: str
    title: str
    category: str                 # email | dns | web | tls | surface | governance | exposure | credential
    severity: str                 # info | low | medium | high | critical
    severity_score: int           # 1..5, context-adjusted
    evidence: str
    risk: str
    nis2_measure: str             # Art. 21(2) letter + short text
    iso_control: str
    service: str                  # Cyber Defencely service that remediates it
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
            "nis2_measure": self.nis2_measure,
            "iso_control": self.iso_control,
            "cyberdefencely_service": self.service,
            "remediation": self.remediation,
            "talking_point": self.talking_point,
            "source": self.source,
        }


@dataclass
class ProspectReport:
    company: Company
    nis2: Nis2Verdict
    email: EmailSecuritySignal
    ciso: CisoSignal
    fit_score: float = 0.0
    reasons: list[str] = field(default_factory=list)

    def to_row(self) -> dict:
        """Flatten to a single CSV-friendly record."""
        leader = next((p for p in self.ciso.people if p.role_tier == "leader"), None)
        return {
            "name": self.company.name,
            "domain": self.company.domain or "",
            "org_number": self.company.org_number or "",
            "employees": self.company.employees if self.company.employees is not None else "",
            "fit_score": round(self.fit_score, 1),
            "nis2_verdict": self.nis2.verdict,
            "nis2_sector": self.nis2.sector or "",
            "email_weakness": self.email.weakness,
            "dmarc_policy": self.email.dmarc_policy or "",
            "ciso_status": self.ciso.status,
            "ciso_confidence": round(self.ciso.confidence, 2),
            "ciso_name": leader.name if leader else "",
            "ciso_title": leader.title if leader else "",
            "verify_ciso": "yes" if self.ciso.verify_recommended else "no",
            "reasons": "; ".join(self.reasons),
        }

    def to_dict(self) -> dict:
        return asdict(self)
