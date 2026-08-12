from __future__ import annotations

"""Orchestrator: run every passive collector for a company and return the
enriched, context-mapped Findings.

Network collectors read public DNS / TLS / HTTP / CT / index data. Signal-
derived findings (email auth, CISO gap, NIS2 readiness) are folded in from
values already computed elsewhere so the vulnerability inventory is unified.
"""

from typing import Optional

from ..context_map import enrich
from ..models import Company, EmailSecuritySignal, Finding
from . import ct_surface, dns_hardening, security_txt, shodan_exposure, web_headers


def _email_codes(sig: EmailSecuritySignal) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if sig.has_spf is False:
        out.append(("EMAIL_SPF_MISSING", "No SPF record"))
    if sig.has_dmarc is False:
        out.append(("EMAIL_DMARC_MISSING", "No DMARC record"))
    elif sig.dmarc_policy in (None, "none"):
        out.append(("EMAIL_DMARC_UNENFORCED", "DMARC policy is p=none (monitor only)"))
    return out


def collect(
    company: Company,
    *,
    email_sig: Optional[EmailSecuritySignal] = None,
    ciso_status: Optional[str] = None,
    nis2_verdict: Optional[str] = None,
    run_network: bool = True,
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []

    # governance / compliance (from already-computed signals)
    if nis2_verdict in ("in_scope", "likely_in_scope"):
        pairs.append(("GOV_NIS2_UNREADY", f"NIS2 {nis2_verdict.replace('_', ' ')}; readiness unverified"))
    if ciso_status in ("none_found", "uncertain"):
        pairs.append(("GOV_NO_CISO", "No clearly-visible security leader (see CISO detection)"))
    if email_sig is not None:
        pairs += _email_codes(email_sig)

    # passive network collectors
    if run_network and company.domain:
        d = company.domain
        for mod in (dns_hardening, web_headers, security_txt, ct_surface, shodan_exposure):
            try:
                pairs += mod.scan(d)
            except Exception:
                continue
    return pairs


def findings_for(company: Company, pairs: list[tuple[str, str]]) -> list[Finding]:
    seen: set[str] = set()
    findings: list[Finding] = []
    for code, evidence in pairs:
        if code in seen:
            continue
        seen.add(code)
        f = enrich(code, evidence, company)
        if f:
            findings.append(f)
    findings.sort(key=lambda f: f.severity_score, reverse=True)
    return findings
