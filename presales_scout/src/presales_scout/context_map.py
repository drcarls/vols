from __future__ import annotations

"""Context mapping: raw finding code -> business & compliance context.

This is the layer that makes a vulnerability inventory *sellable*. A collector
emits a bare code like ``EMAIL_DMARC_MISSING``; here we attach what it means,
which NIS2 obligation (Swedish Cybersäkerhetslagen implements NIS2 Art. 21(2))
and ISO 27001:2022 control it maps to, a base severity, the Cyber Defencely
service that remediates it, and a sales talking point.

Severity is then *context-adjusted*: for critical-infrastructure sectors
(energy, transport, water, digital infra) technical weaknesses are escalated
one notch, because the same misconfiguration carries more consequence — and
more regulatory exposure — for a NIS2 essential entity.

NIS2 Art. 21(2) measures referenced:
  (a) risk analysis & information-system security policies
  (b) incident handling
  (c) business continuity / backup / crisis management
  (d) supply-chain security
  (e) security in acquisition, development & maintenance (incl. vuln handling)
  (f) policies to assess effectiveness of measures
  (g) basic cyber hygiene & security training
  (h) cryptography and encryption
  (i) HR security, access control, asset management
  (j) MFA, secured voice/video/text, emergency communications
"""

from .models import Company, Finding

SEVERITY_ORDER = ["info", "low", "medium", "high", "critical"]
CRITICAL_INFRA_SECTORS = {"Energy", "Transport", "Drinking water", "Waste water", "Digital infrastructure"}

# code -> context. {sev} is the BASE severity (1..5); escalation happens in enrich().
CATALOG: dict[str, dict] = {
    "EMAIL_DMARC_MISSING": dict(
        title="No DMARC record", category="email", base=3,
        risk="Attackers can spoof the domain in phishing with no receiver-side rejection.",
        nis2="(g) basic cyber hygiene", iso="A.5.14 / A.8.16 (secure information transfer, monitoring)",
        service="Rapid Cybersecurity Assessment (email-security quick win)",
        remediation="Publish DMARC and ramp to p=reject after monitoring.",
        talking="Your domain can be spoofed for phishing today — a fixable, high-visibility gap."),
    "EMAIL_DMARC_UNENFORCED": dict(
        title="DMARC not enforced (p=none)", category="email", base=2,
        risk="DMARC is monitor-only; spoofed mail is still delivered.",
        nis2="(g) basic cyber hygiene", iso="A.8.16 (monitoring activities)",
        service="Rapid Cybersecurity Assessment (email-security quick win)",
        remediation="Move DMARC policy from p=none to quarantine, then reject.",
        talking="You publish DMARC but don't enforce it — half-protected against spoofing."),
    "EMAIL_SPF_MISSING": dict(
        title="No SPF record", category="email", base=3,
        risk="No sender authorisation; trivial sender forgery.",
        nis2="(g) basic cyber hygiene", iso="A.5.14 (information transfer)",
        service="Rapid Cybersecurity Assessment", remediation="Publish an SPF record with -all.",
        talking="Basic sender authentication is missing."),
    "EMAIL_SPF_SOFTFAIL": dict(
        title="SPF not hard-fail (~all/?all)", category="email", base=1,
        risk="Softfail lets spoofed mail through with only a soft mark.",
        nis2="(g) basic cyber hygiene", iso="A.5.14 (information transfer)",
        service="Rapid Cybersecurity Assessment",
        remediation="Tighten SPF to -all once senders are inventoried.",
        talking="Your SPF is permissive (~all) rather than enforcing (-all)."),
    "EMAIL_MTASTS_MISSING": dict(
        title="No MTA-STS policy", category="email", base=2,
        risk="Inbound mail can be downgraded to cleartext by an on-path attacker.",
        nis2="(h) cryptography & encryption", iso="A.8.24 (use of cryptography)",
        service="Rapid Cybersecurity Assessment",
        remediation="Publish an MTA-STS policy in enforce mode.",
        talking="Inbound email TLS isn't enforced — interceptable in transit."),
    "EMAIL_TLSRPT_MISSING": dict(
        title="No TLS-RPT reporting", category="email", base=1,
        risk="No visibility into failed inbound mail-TLS negotiations.",
        nis2="(f) assessing effectiveness of measures", iso="A.8.16 (monitoring)",
        service="Rapid Cybersecurity Assessment", remediation="Publish a TLS-RPT record.",
        talking="No reporting on mail-transport security failures."),
    "DNS_DNSSEC_MISSING": dict(
        title="DNSSEC not enabled", category="dns", base=2,
        risk="DNS answers can be forged/poisoned; no origin authentication.",
        nis2="(h) cryptography & encryption", iso="A.8.24 (use of cryptography)",
        service="Rapid Cybersecurity Assessment",
        remediation="Enable DNSSEC signing at the zone and registrar.",
        talking="DNS responses aren't cryptographically signed."),
    "DNS_CAA_MISSING": dict(
        title="No CAA record", category="dns", base=1,
        risk="Any CA may issue certificates for the domain (mis-issuance risk).",
        nis2="(h) cryptography & encryption", iso="A.8.24 (use of cryptography)",
        service="Rapid Cybersecurity Assessment",
        remediation="Publish CAA records restricting issuance to approved CAs.",
        talking="Certificate issuance isn't restricted to your CAs."),
    "WEB_HSTS_MISSING": dict(
        title="No HSTS header", category="web", base=2,
        risk="Users can be downgraded to HTTP and man-in-the-middled.",
        nis2="(h) cryptography & encryption", iso="A.8.24 (use of cryptography)",
        service="Rapid Cybersecurity Assessment", remediation="Send Strict-Transport-Security.",
        talking="The site doesn't force HTTPS via HSTS."),
    "WEB_CSP_MISSING": dict(
        title="No Content-Security-Policy", category="web", base=2,
        risk="No defence-in-depth against XSS / content injection.",
        nis2="(e) secure development & maintenance", iso="A.8.26 (application security requirements)",
        service="Rapid Cybersecurity Assessment", remediation="Deploy a Content-Security-Policy.",
        talking="No CSP — weaker against cross-site scripting."),
    "WEB_SECURITY_HEADERS_WEAK": dict(
        title="Missing hardening headers (X-Frame-Options / nosniff)", category="web", base=1,
        risk="Clickjacking and MIME-sniffing exposure.",
        nis2="(e) secure development & maintenance", iso="A.8.26 (application security requirements)",
        service="Rapid Cybersecurity Assessment", remediation="Add X-Frame-Options and X-Content-Type-Options.",
        talking="Standard browser hardening headers are absent."),
    "WEB_VERSION_DISCLOSURE": dict(
        title="Software version disclosed", category="web", base=2,
        risk="Version banners let attackers target known CVEs directly.",
        nis2="(e) secure development & maintenance", iso="A.8.9 (configuration management)",
        service="Rapid Cybersecurity Assessment",
        remediation="Suppress Server / X-Powered-By version banners.",
        talking="Your stack is advertising its exact version to attackers."),
    "WEB_COMPONENT_EOL": dict(
        title="End-of-life component in use", category="web", base=4,
        risk="Unsupported software receives no security patches.",
        nis2="(e) secure development & maintenance", iso="A.8.8 (management of technical vulnerabilities)",
        service="Rapid Cybersecurity Assessment + remediation advisory",
        remediation="Upgrade the component to a supported release.",
        talking="You're running end-of-life software with no security patches."),
    "MATURITY_SECURITYTXT_MISSING": dict(
        title="No security.txt (RFC 9116)", category="web", base=1,
        risk="No published channel for coordinated vulnerability disclosure.",
        nis2="(e) vulnerability handling & disclosure", iso="A.5.5 / A.6.8 (authorities, reporting)",
        service="Rapid Cybersecurity Assessment",
        remediation="Publish /.well-known/security.txt with a disclosure contact.",
        talking="No way for researchers to report a vulnerability to you."),
    "SURFACE_SUBDOMAINS": dict(
        title="Large external attack surface", category="surface", base=2,
        risk="More exposed hosts (dev/staging/vpn/admin) = more to defend and miss.",
        nis2="(a) risk analysis & (i) asset management", iso="A.5.9 (inventory of assets)",
        service="Rapid Cybersecurity Assessment (external attack-surface review)",
        remediation="Inventory and retire/segment exposed subdomains.",
        talking="A wide public footprint — do you have an inventory of all of it?"),
    "SURFACE_TAKEOVER_CANDIDATE": dict(
        title="Possible subdomain-takeover candidate", category="surface", base=4,
        risk="A dangling DNS record can be claimed to serve content on your domain.",
        nis2="(i) asset management", iso="A.5.9 (inventory of assets)",
        service="Rapid Cybersecurity Assessment", remediation="Remove dangling CNAMEs / reclaim resources.",
        talking="A dangling subdomain could be hijacked under your brand."),
    "GOV_NO_CISO": dict(
        title="No publicly visible CISO / security leader", category="governance", base=3,
        risk="Under Cybersäkerhetslagen the management body is accountable for security; a leadership gap is a governance risk.",
        nis2="(a) governance & security policies", iso="A.5.1 / A.5.2 (policies, roles & responsibilities)",
        service="CISO-as-a-Service + Leadership training",
        remediation="Appoint / retain security leadership; assign board accountability.",
        talking="No security leader on show while NIS2 makes the board personally accountable."),
    "GOV_NIS2_UNREADY": dict(
        title="In NIS2 scope, readiness unverified", category="governance", base=3,
        risk="Non-compliance exposure under Cybersäkerhetslagen (in force since 15 Jan 2026).",
        nis2="(a) risk management & (f) effectiveness", iso="A.5.1 (policies for information security)",
        service="Rapid Cybersecurity Assessment (NIS2 gap analysis)",
        remediation="Run a NIS2 gap assessment and remediation roadmap.",
        talking="You're a NIS2 essential/important entity — is your compliance evidenced?"),
    "EXPOSURE_SERVICE_OPEN": dict(
        title="Exposed service on the public internet", category="exposure", base=4,
        risk="Directly reachable services (RDP/DB/admin) are prime intrusion points.",
        nis2="(i) access control & asset management", iso="A.8.20 / A.8.9 (network security, config)",
        service="Rapid Cybersecurity Assessment (urgent) + Team-as-a-Service",
        remediation="Remove from public exposure; put behind VPN/zero-trust.",
        talking="A sensitive service is reachable from the open internet right now."),
    "EXPOSURE_OT_ICS": dict(
        title="Exposed OT/ICS system", category="exposure", base=5,
        risk="Internet-exposed industrial control systems are a safety and continuity threat.",
        nis2="(a) risk analysis & (c) business continuity", iso="A.8.20 (network security)",
        service="Rapid Cybersecurity Assessment (critical) + Team-as-a-Service",
        remediation="Isolate OT from the internet; segment IT/OT networks.",
        talking="An industrial control system appears internet-exposed — a critical safety risk."),
    "SUPPLY_UNMANAGED": dict(
        title="Unmanaged third-party / supplier dependencies", category="supply_chain", base=2,
        risk="Each external supplier that runs in-page or handles data is an attack path the entity is accountable for.",
        nis2="(d) supply-chain security", iso="A.5.19 / A.5.21 (supplier relationships, ICT supply chain)",
        service="Supply-chain / third-party risk assessment (Rapid Assessment + Team-as-a-Service)",
        remediation="Inventory suppliers, set security requirements, and monitor them continuously.",
        talking="Under NIS2 you're accountable for these suppliers' security — is there a third-party risk process?"),
    "CRED_BREACH": dict(
        title="Breached employee credentials exposed", category="credential", base=3,
        risk="Leaked credentials enable account takeover and initial access.",
        nis2="(i) access control & (j) MFA", iso="A.5.17 / A.8.5 (authentication information)",
        service="Security Awareness Training + access-control review",
        remediation="Force resets, enforce MFA, monitor for credential reuse.",
        talking="Staff credentials are circulating in breach dumps — enforce MFA."),
}


def _clamp(i: int) -> int:
    return max(1, min(5, i))


def enrich(code: str, evidence: str, company: Company) -> Finding | None:
    spec = CATALOG.get(code)
    if not spec:
        return None
    score = spec["base"]
    # Context adjustment: escalate technical weaknesses for critical-infra sectors.
    sector = None
    from .collectors import nis2 as _nis2
    sector = _nis2.match_sector(company.sni_code)
    if sector in CRITICAL_INFRA_SECTORS and spec["category"] in ("email", "dns", "web", "tls", "surface", "exposure", "supply_chain"):
        score = _clamp(score + 1)
    severity = SEVERITY_ORDER[score - 1]
    return Finding(
        company=company.name, domain=company.domain, finding_id=code,
        title=spec["title"], category=spec["category"], severity=severity, severity_score=score,
        evidence=evidence, risk=spec["risk"], nis2_measure=f"Art. 21(2){spec['nis2']}",
        iso_control=spec["iso"], service=spec["service"], remediation=spec["remediation"],
        talking_point=spec["talking"],
    )
