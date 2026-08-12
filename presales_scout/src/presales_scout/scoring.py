from __future__ import annotations

"""Combine the three signals into a single prospect fit score (0-100).

Higher = better prospect for Cyber Defencely. The NIS2 verdict is the
qualifier (out-of-scope firms are heavily deprioritized); weak email
hygiene and a missing visible CISO are the pitch material that push a
qualified firm up the list.
"""

from .models import CisoSignal, EmailSecuritySignal, Nis2Verdict, ProspectReport, Company

NIS2_WEIGHTS = {"in_scope": 45, "likely_in_scope": 28, "unknown": 10, "out_of_scope": -100}
EMAIL_WEIGHTS = {"weak": 25, "partial": 12, "strong": 0, "unknown": 5}
CISO_WEIGHTS = {"none_found": 30, "uncertain": 15, "visible": 0}


def score(company: Company, nis2: Nis2Verdict, email: EmailSecuritySignal, ciso: CisoSignal) -> ProspectReport:
    reasons: list[str] = []
    total = 0.0

    total += NIS2_WEIGHTS.get(nis2.verdict, 0)
    if nis2.verdict in ("in_scope", "likely_in_scope"):
        reasons.append(f"NIS2 {nis2.verdict.replace('_', ' ')} ({nis2.sector})")
    elif nis2.verdict == "out_of_scope":
        reasons.append("Not in NIS2 scope on current data")

    total += EMAIL_WEIGHTS.get(email.weakness, 0)
    if email.weakness == "weak":
        reasons.append("Weak email security (" + ", ".join(email.findings) + ")")
    elif email.weakness == "partial":
        reasons.append("Partial email security")

    total += CISO_WEIGHTS.get(ciso.status, 0)
    if ciso.status == "none_found":
        reasons.append("No publicly visible CISO -> CISO-as-a-Service opening")
    elif ciso.status == "uncertain":
        reasons.append("No clear security leader identified")
    elif ciso.status == "visible":
        leader = next((p for p in ciso.people if p.role_tier == "leader"), None)
        if leader:
            reasons.append(f"Has a visible security leader ({leader.name})")

    total = max(0.0, min(100.0, total))
    return ProspectReport(
        company=company, nis2=nis2, email=email, ciso=ciso, fit_score=total, reasons=reasons
    )


def brief(report: ProspectReport) -> str:
    """One-paragraph pre-sales brief mapping findings to services."""
    c = report.company
    lines = [f"{c.name} — fit score {report.fit_score:.0f}/100"]
    lines.append("  " + "; ".join(report.reasons))
    pitch: list[str] = []
    if report.nis2.verdict in ("in_scope", "likely_in_scope"):
        pitch.append("Rapid Cybersecurity Assessment (NIS2 readiness)")
    if report.ciso.status in ("none_found", "uncertain"):
        pitch.append("CISO-as-a-Service")
    if report.email.weakness in ("weak", "partial"):
        pitch.append("email-security quick win as a door-opener")
    if pitch:
        lines.append("  Suggested angle: " + ", ".join(pitch) + ".")
    if report.ciso.verify_recommended and report.ciso.status != "visible":
        lines.append("  (Verify CISO absence by hand before outreach.)")
    return "\n".join(lines)
