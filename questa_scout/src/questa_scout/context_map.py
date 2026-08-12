from __future__ import annotations

"""Context mapping: raw signal -> business & compliance context.

This is the layer that makes a prospect list *sellable*. A collector emits a
bare signal ("no governance owner found", "hiring for LLM roles"); here we
attach what it means, the US regulation it maps to (HIPAA, GLBA, state
privacy such as CCPA/CPRA -- and the EU AI Act where there's an EU nexus),
a severity, the Questa product that addresses it, and a sales talking point.

Severity is context-adjusted by data sensitivity: the same ungoverned-AI
gap carries more consequence for a PHI handler than for a generic consumer-
PII processor, so PHI escalates a notch.
"""

from .models import Finding, ProspectReport

SEVERITY_ORDER = ["info", "low", "medium", "high", "critical"]

# code -> context. {base} is the BASE severity (1..5); escalation in enrich().
CATALOG: dict[str, dict] = {
    "AI_SHADOW_RISK": dict(
        title="Active AI adoption with no governance owner", category="governance", base=4,
        risk="Regulated data is flowing to LLMs while no one owns AI governance -- "
             "the textbook shadow-AI exposure Questa is built to close.",
        regulation="HIPAA 164.308(a)(1) / GLBA Safeguards Rule / state privacy (CCPA/CPRA)",
        product="Questa Blackbox (self-hosted redaction)",
        remediation="Insert a redaction/anonymization layer before any model; assign AI-governance ownership.",
        talking="You're putting regulated data into AI with no governance owner -- that's the breach and the fine in one gap."),
    "AI_NO_GOVERNANCE_OWNER": dict(
        title="No visible privacy / AI-governance owner", category="governance", base=3,
        risk="No accountable owner for how AI touches regulated data; governance and audit gap.",
        regulation="GLBA Safeguards Rule 314.4(a) / state privacy accountability / EU AI Act Art. 26 (if EU nexus)",
        product="Questa Blackbox + governance dashboard",
        remediation="Appoint/retain a privacy or AI-governance owner; stand up a governance dashboard.",
        talking="No DPO or AI-governance lead on show while AI adoption accelerates -- who signs off on what the model sees?"),
    "AI_ADOPTION_ACTIVE": dict(
        title="Actively hiring/deploying AI", category="adoption", base=3,
        risk="Live AI projects mean live data exposure now -- redaction is needed before, not after.",
        regulation="HIPAA / GLBA / state privacy (data minimization)",
        product="Questa (Blackbox / Developer / Cloud by segment)",
        remediation="Route sensitive data through anonymization before it reaches any LLM.",
        talking="Your AI build-out is underway -- redact at the source before the first prompt leaks."),
    "AI_PUBLIC_CHATBOT_UNREDACTED": dict(
        title="Customer-facing chatbot with no visible privacy control", category="exposure", base=4,
        risk="Free-text chat is ungoverned PII/PHI ingestion straight into a model.",
        regulation="GDPR/CCPA data minimization; HIPAA if health context",
        product="Questa Developer (API redaction in the message path)",
        remediation="Redact inbound messages before the model; log for compliance.",
        talking="Every message your bot accepts is ungoverned data ingestion -- redact before the model, not after."),
    "DATA_PHI_HANDLER": dict(
        title="Handles PHI (HIPAA)", category="data", base=3,
        risk="Protected Health Information in AI workflows without de-identification is a HIPAA exposure.",
        regulation="HIPAA Privacy & Security Rules; 164.514 de-identification",
        product="Questa Blackbox (self-hosted, HIPAA-aligned)",
        remediation="De-identify PHI before AI processing; keep a BAA-compatible on-prem deployment.",
        talking="PHI in a prompt is a disclosure -- de-identify before the model sees it, on infrastructure you control."),
    "DATA_FINANCIAL_HANDLER": dict(
        title="Handles financial / customer data (GLBA)", category="data", base=3,
        risk="Nonpublic personal financial information in AI workflows triggers GLBA safeguards duties.",
        regulation="GLBA Safeguards Rule (16 CFR 314)",
        product="Questa Blackbox / Developer",
        remediation="Anonymize NPI before model calls; evidence safeguards in a governance dashboard.",
        talking="Customer financial data in AI is a GLBA safeguards question -- can you evidence the control?"),
    "DATA_LEGAL_PRIVILEGED": dict(
        title="Handles privileged / M&A-confidential data", category="data", base=3,
        risk="Privileged or deal-confidential material sent to a shared LLM risks waiver and leakage.",
        regulation="Attorney-client privilege / confidentiality duties; state privacy",
        product="Questa Blackbox (self-hosted)",
        remediation="Keep privileged content in a self-hosted, redacting deployment; no third-party model exposure.",
        talking="Privileged material in a public model can waive privilege -- keep it in a box you control."),
    "DATA_CONSUMER_PII": dict(
        title="Processes consumer PII (state privacy)", category="data", base=2,
        risk="Consumer PII in AI workflows engages CCPA/CPRA and other state-privacy obligations.",
        regulation="CCPA/CPRA and equivalent state laws",
        product="Questa Developer / Cloud",
        remediation="Anonymize PII before model calls; maintain processing records.",
        talking="Consumer PII flowing into AI is squarely in state-privacy scope -- redact before it leaves your perimeter."),
}


def _clamp(i: int) -> int:
    return max(1, min(5, i))


def enrich(code: str, evidence: str, report: ProspectReport) -> Finding | None:
    spec = CATALOG.get(code)
    if not spec:
        return None
    score = spec["base"]
    # Context adjustment: escalate for PHI (highest-sensitivity) handlers.
    if report.data_scope.sensitivity >= 4:
        score = _clamp(score + 1)
    severity = SEVERITY_ORDER[score - 1]
    c = report.company
    # Prefer the routed product where the catalog entry is segment-generic.
    product = spec["product"]
    if report.product and "by segment" in product:
        product = report.product
    return Finding(
        company=c.name, domain=c.domain, finding_id=code,
        title=spec["title"], category=spec["category"], severity=severity, severity_score=score,
        evidence=evidence, risk=spec["risk"], regulation=spec["regulation"],
        product=product, remediation=spec["remediation"], talking_point=spec["talking"],
    )


def derive_findings(report: ProspectReport) -> list[Finding]:
    """Inspect a scored report and emit the applicable, enriched findings,
    most severe first."""
    codes: list[tuple[str, str]] = []
    ds, ad, gov = report.data_scope, report.adoption, report.governance

    # The headline: active AI + no owner.
    if ad.level in ("active", "emerging") and gov.status in ("none_found", "uncertain"):
        codes.append(("AI_SHADOW_RISK", f"AI adoption {ad.level}; governance {gov.status}"))

    if gov.status in ("none_found", "uncertain"):
        codes.append(("AI_NO_GOVERNANCE_OWNER", f"governance {gov.status} (conf {gov.confidence:.2f})"))

    if ad.level in ("active", "emerging"):
        codes.append(("AI_ADOPTION_ACTIVE", "; ".join(ad.findings) or ad.level))

    if ad.chatbot:
        codes.append(("AI_PUBLIC_CHATBOT_UNREDACTED", "chatbot widget on homepage"))

    data_code = {
        "PHI": "DATA_PHI_HANDLER",
        "financial": "DATA_FINANCIAL_HANDLER",
        "legal_privileged": "DATA_LEGAL_PRIVILEGED",
        "consumer_pii": "DATA_CONSUMER_PII",
    }.get(ds.data_class or "")
    if data_code and ds.verdict in ("in_scope", "likely_in_scope"):
        codes.append((data_code, f"{ds.sector} under {ds.regime}"))

    findings: list[Finding] = []
    seen: set[str] = set()
    for code, evidence in codes:
        if code in seen:
            continue
        seen.add(code)
        f = enrich(code, evidence, report)
        if f:
            findings.append(f)
    findings.sort(key=lambda f: f.severity_score, reverse=True)
    return findings
