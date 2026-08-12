from __future__ import annotations

"""Combine the three signals into a single prospect fit score (0-100).

Higher = better prospect for Questa AI. The data-scope verdict is the
qualifier (organizations that don't handle regulated data are heavily
deprioritized); active AI adoption is the buy-now trigger; a missing
privacy/AI-governance owner is the opening. Data sensitivity (PHI > financial
/ legal > consumer PII) breaks ties toward the highest-stakes accounts.
"""

from .models import (
    AiAdoptionSignal,
    Company,
    DataScopeVerdict,
    GovernanceSignal,
    ProspectReport,
)
from .routing import route_product

# Components are sized so a maxed prospect lands at ~100 without the clamp
# doing the work: qualifier + sensitivity + adoption intensity + governance.
# Nothing saturates until PHI + full adoption + no owner, which is rare.
SCOPE_WEIGHTS = {"in_scope": 30, "likely_in_scope": 20, "unknown": 6, "out_of_scope": -100}
GOVERNANCE_WEIGHTS = {"none_found": 25, "uncertain": 12, "governed": 0}
# Data sensitivity (0..4) is a first-class ranking axis, not just a tie-break.
SENSITIVITY_WEIGHTS = {4: 15, 3: 10, 2: 5, 1: 2, 0: 0}
ADOPTION_MAX = 30          # scaled by intensity (0..5); "unknown" gets a small floor
ADOPTION_UNKNOWN = 5.0
ADOPTION_INTENSITY_MAX = 5


def _adoption_points(adoption: AiAdoptionSignal) -> float:
    if adoption.level == "unknown":
        return ADOPTION_UNKNOWN
    return ADOPTION_MAX * (adoption.intensity() / ADOPTION_INTENSITY_MAX)


def score(
    company: Company,
    data_scope: DataScopeVerdict,
    adoption: AiAdoptionSignal,
    governance: GovernanceSignal,
) -> ProspectReport:
    reasons: list[str] = []
    total = 0.0

    total += SCOPE_WEIGHTS.get(data_scope.verdict, 0)
    if data_scope.verdict in ("in_scope", "likely_in_scope"):
        reasons.append(
            f"Regulated data: {data_scope.data_class} ({data_scope.sector}, {data_scope.regime})"
        )
        total += SENSITIVITY_WEIGHTS.get(data_scope.sensitivity, 0)
    elif data_scope.verdict == "out_of_scope":
        reasons.append("Not a regulated-data sector on current data")

    total += _adoption_points(adoption)
    if adoption.level == "active":
        reasons.append("Active AI adoption (" + "; ".join(adoption.findings) + ")")
    elif adoption.level == "emerging":
        reasons.append("Emerging AI adoption")

    total += GOVERNANCE_WEIGHTS.get(governance.status, 0)
    if governance.status == "none_found":
        reasons.append("No visible privacy/AI-governance owner -> Questa opening")
    elif governance.status == "uncertain":
        reasons.append("No clear governance owner identified")
    elif governance.status == "governed":
        leader = next((p for p in governance.people if p.role_tier == "leader"), None)
        if leader:
            reasons.append(f"Has a visible governance owner ({leader.name})")

    total = max(0.0, min(100.0, total))
    product = route_product(company, data_scope)
    return ProspectReport(
        company=company,
        data_scope=data_scope,
        adoption=adoption,
        governance=governance,
        product=product,
        fit_score=total,
        reasons=reasons,
    )


def brief(report: ProspectReport) -> str:
    """One-paragraph pre-sales brief mapping signals to Questa products."""
    from .context_map import derive_findings

    c = report.company
    lines = [f"{c.name} - fit score {report.fit_score:.0f}/100  [lead: {report.product}]"]
    lines.append("  " + "; ".join(report.reasons))

    findings = derive_findings(report)
    if findings:
        top = findings[0]
        lines.append(f"  Angle: {top.talking_point}")
        lines.append(
            "  Maps to: "
            + ", ".join(f"{f.finding_id} ({f.severity})" for f in findings[:3])
        )
    if report.governance.verify_recommended and report.governance.status != "governed":
        lines.append("  (Verify governance-owner absence by hand before outreach.)")
    return "\n".join(lines)
