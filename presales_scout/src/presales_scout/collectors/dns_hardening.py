from __future__ import annotations

"""Passive DNS-hardening checks: DNSSEC, CAA, MTA-STS, TLS-RPT, SPF strictness.

All read public DNS over DoH. Returns bare (code, evidence) pairs for the
context map to enrich.
"""

from . import _doh


def scan(domain: str) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    d = domain.strip().lower()

    if not _doh.has_record(d, "DNSKEY"):
        findings.append(("DNS_DNSSEC_MISSING", "No DNSKEY record found for the zone"))

    if not _doh.resolve(d, "CAA"):
        findings.append(("DNS_CAA_MISSING", "No CAA record restricting certificate issuance"))

    # MTA-STS: policy is signalled by a _mta-sts TXT record (v=STSv1)
    mta = [t for t in _doh.resolve(f"_mta-sts.{d}", "TXT") if t.lower().startswith("v=stsv1")]
    if not mta:
        findings.append(("EMAIL_MTASTS_MISSING", "No _mta-sts TXT policy record"))

    tlsrpt = [t for t in _doh.resolve(f"_smtp._tls.{d}", "TXT") if t.lower().startswith("v=tlsrptv1")]
    if not tlsrpt:
        findings.append(("EMAIL_TLSRPT_MISSING", "No _smtp._tls TXT reporting record"))

    # SPF strictness: present but softfail (~all) or neutral (?all) rather than -all
    spf = [t for t in _doh.resolve(d, "TXT") if t.lower().startswith("v=spf1")]
    if spf:
        pol = spf[0].lower()
        if "~all" in pol or "?all" in pol:
            findings.append(("EMAIL_SPF_SOFTFAIL", f"SPF present but not hard-fail: '{spf[0][-12:]}'"))

    return findings
