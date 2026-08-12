from __future__ import annotations

"""Automated context mapping.

Replaces the hand-written per-finding CATALOG in context_map.py. A finding is
tagged with ONE control theme (THEME_OF); everything else — the NIS2 measure,
ISO control, base severity, and Cyber Defencely service — is looked up from the
curated crosswalk (kb/crosswalk.yaml). Adding a new finding costs one line here,
not a full hand-authored mapping.

Two layers, deliberately separated so the automation can't fabricate compliance
claims (the lesson from the supplier categoriser):

  1. Deterministic backbone — theme -> crosswalk -> frameworks/service/severity.
     Runs with no LLM, fully auditable, no invention possible.
  2. LLM narrative (optional, key-gated) — writes ONLY the prose (risk sentence,
     remediation, sales talking point) in Cyber Defencely's voice, grounded on
     the evidence. It is never asked for a control ID, so it cannot hallucinate
     one. Falls back to a deterministic template when no ANTHROPIC_API_KEY.
"""

import json
import os

from .config import project_root
from .models import Company, Finding
from .collectors import nis2 as _nis2

CRITICAL_INFRA_SECTORS = {"Energy", "Transport", "Drinking water", "Waste water", "Digital infrastructure"}
SEVERITY_ORDER = ["info", "low", "medium", "high", "critical"]

# finding code -> control theme. This is the ONLY per-finding data the engine
# needs; the rich mapping lives in the crosswalk, keyed by theme.
THEME_OF: dict[str, str] = {
    "EMAIL_DMARC_MISSING": "email_authentication",
    "EMAIL_DMARC_UNENFORCED": "email_authentication",
    "EMAIL_SPF_MISSING": "email_authentication",
    "EMAIL_SPF_SOFTFAIL": "email_authentication",
    "EMAIL_MTASTS_MISSING": "transport_encryption",
    "EMAIL_TLSRPT_MISSING": "transport_encryption",
    "DNS_DNSSEC_MISSING": "transport_encryption",
    "DNS_CAA_MISSING": "transport_encryption",
    "WEB_HSTS_MISSING": "transport_encryption",
    "WEB_CSP_MISSING": "vulnerability_management",
    "WEB_SECURITY_HEADERS_WEAK": "vulnerability_management",
    "WEB_VERSION_DISCLOSURE": "vulnerability_management",
    "WEB_COMPONENT_EOL": "vulnerability_management",
    "MATURITY_SECURITYTXT_MISSING": "vulnerability_disclosure",
    "SURFACE_SUBDOMAINS": "attack_surface",
    "SURFACE_TAKEOVER_CANDIDATE": "attack_surface",
    "GOV_NO_CISO": "security_governance",
    "GOV_NIS2_UNREADY": "security_governance",
    "EXPOSURE_SERVICE_OPEN": "exposed_service",
    "EXPOSURE_OT_ICS": "exposed_ot",
    "CRED_BREACH": "credential_exposure",
    "SUPPLY_UNMANAGED": "supply_chain",
    "SUPPLY_PROCUREMENT_CRITICAL": "supply_chain",
}

# The few findings whose severity differs from their theme's base.
SEVERITY_OVERRIDE: dict[str, int] = {
    "WEB_COMPONENT_EOL": 4,
    "SURFACE_TAKEOVER_CANDIDATE": 4,
    "EMAIL_TLSRPT_MISSING": 1,
    "DNS_CAA_MISSING": 1,
    "WEB_SECURITY_HEADERS_WEAK": 1,
}

# Human titles where a derived-from-code title would read poorly. Optional —
# unknown codes fall back to a title derived from the code.
TITLES: dict[str, str] = {
    "EMAIL_DMARC_MISSING": "No DMARC record",
    "EMAIL_DMARC_UNENFORCED": "DMARC not enforced (p=none)",
    "EMAIL_MTASTS_MISSING": "No MTA-STS policy",
    "DNS_DNSSEC_MISSING": "DNSSEC not enabled",
    "WEB_VERSION_DISCLOSURE": "Software version disclosed",
    "WEB_COMPONENT_EOL": "End-of-life component in use",
    "MATURITY_SECURITYTXT_MISSING": "No security.txt (RFC 9116)",
    "GOV_NO_CISO": "No publicly visible CISO / security leader",
    "GOV_NIS2_UNREADY": "In NIS2 scope, readiness unverified",
    "EXPOSURE_SERVICE_OPEN": "Exposed service on the public internet",
    "EXPOSURE_OT_ICS": "Exposed OT/ICS system",
    "SUPPLY_UNMANAGED": "Unmanaged third-party / supplier dependencies",
    "SUPPLY_PROCUREMENT_CRITICAL": "Outsources NIS2-critical systems via public procurement",
}

_CROSSWALK: dict | None = None


def _crosswalk() -> dict:
    global _CROSSWALK
    if _CROSSWALK is None:
        import yaml
        with open(project_root() / "kb" / "crosswalk.yaml", encoding="utf-8") as f:
            _CROSSWALK = yaml.safe_load(f)["themes"]
    return _CROSSWALK


def _title(code: str) -> str:
    return TITLES.get(code) or code.replace("_", " ").title()


def _clamp(i: int) -> int:
    return max(1, min(5, i))


def enrich(code: str, evidence: str, company: Company) -> Finding | None:
    """Map a raw (code, evidence) to a fully context-mapped Finding.

    Drop-in compatible with context_map.enrich, but driven by the crosswalk
    instead of a hand-written catalog — so a code the static catalog never
    listed still maps, as long as it has a theme.
    """
    theme = THEME_OF.get(code)
    if not theme:
        return None
    spec = _crosswalk()[theme]

    # --- deterministic backbone: severity, frameworks, service ---
    score = SEVERITY_OVERRIDE.get(code, spec["base_severity"])
    sector = _nis2.match_sector(company.sni_code)
    if sector in CRITICAL_INFRA_SECTORS and theme not in ("security_governance",):
        score = _clamp(score + 1)
    severity = SEVERITY_ORDER[score - 1]

    # --- narrative: grounded LLM if available, else deterministic template ---
    narrative = _narrative(code, theme, spec, evidence, company)

    return Finding(
        company=company.name, domain=company.domain, finding_id=code,
        title=_title(code), category=theme, severity=severity, severity_score=score,
        evidence=evidence, risk=narrative["risk"],
        nis2_measure=f"Art. 21(2){spec['nis2']}", iso_control=spec["iso"],
        service=spec["service"], remediation=narrative["remediation"],
        talking_point=narrative["talking_point"],
        source="passive_osint+auto_context",
    )


# --------------------------------------------------------------------------- #
# Narrative layer
# --------------------------------------------------------------------------- #

def _template_narrative(code: str, theme: str, spec: dict, evidence: str, company: Company) -> dict:
    """Deterministic fallback narrative (no LLM)."""
    label = spec["label"].lower()
    return {
        "risk": f"{spec['label']} weakness ({evidence}) — a gap in {spec['nis2']} the entity is accountable for.",
        "remediation": f"Address the {label} gap and evidence it against {spec['iso']}.",
        "talking_point": (f"{company.name} has an observable {label} gap that maps to "
                          f"NIS2 Art. 21(2){spec['nis2']} — {spec['service']} closes it."),
    }


def _narrative(code: str, theme: str, spec: dict, evidence: str, company: Company) -> dict:
    """LLM narrative when ANTHROPIC_API_KEY is set; template otherwise.

    The model writes ONLY prose (risk / remediation / talking_point). Framework
    IDs, severity, and the service are fixed deterministically above and passed
    in as grounding — the model is never asked to produce a control ID, so it
    cannot invent one. On any error we fall back to the template.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return _template_narrative(code, theme, spec, evidence, company)
    try:
        import anthropic
    except Exception:
        return _template_narrative(code, theme, spec, evidence, company)

    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "risk": {"type": "string"},
            "remediation": {"type": "string"},
            "talking_point": {"type": "string"},
        },
        "required": ["risk", "remediation", "talking_point"],
    }
    prompt = (
        "You write one-line pre-sales talking points for Cyber Defencely, a Swedish "
        "cybersecurity consultancy selling NIS2-readiness services.\n\n"
        f"Prospect: {company.name} (sector: {_nis2.match_sector(company.sni_code) or 'unknown'}).\n"
        f"Finding: {spec['label']} — {_title(code)}.\n"
        f"Evidence: {evidence}\n"
        f"This maps (already determined — do NOT restate or alter the IDs) to "
        f"NIS2 Art. 21(2){spec['nis2']}, ISO 27001 {spec['iso']}, remediated by "
        f"{spec['service']}.\n\n"
        "Write, grounded only on the evidence above:\n"
        "- risk: one sentence on what an attacker could do / the business consequence.\n"
        "- remediation: one concrete sentence.\n"
        "- talking_point: one punchy sentence a consultant could open a call with.\n"
        "Do not invent facts, control numbers, or CVE IDs not present above."
    )
    try:
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model="claude-opus-5",
            max_tokens=1024,
            thinking={"type": "adaptive"},
            output_config={"format": {"type": "json_schema", "schema": schema}},
            messages=[{"role": "user", "content": prompt}],
        )
        text = next(b.text for b in resp.content if b.type == "text")
        out = json.loads(text)
        if all(k in out and out[k] for k in ("risk", "remediation", "talking_point")):
            return out
    except Exception:
        pass
    return _template_narrative(code, theme, spec, evidence, company)
