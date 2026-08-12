from __future__ import annotations

"""Passive email-security hygiene check via public DNS.

Reads SPF and DMARC TXT records -- pure public DNS, zero legal risk, and
"no DMARC" is a concrete, screenshot-ready finding. DKIM is skipped in v1
because it needs a selector we can't reliably guess.

Two resolvers are supported: dnspython (native UDP/53) and DNS-over-HTTPS
(Google/Cloudflare JSON API). DoH is the default because it works in
sandboxed/proxied environments where UDP/53 is blocked but HTTPS is open.
If neither works the check degrades to an "unknown" signal so the rest of
the pipeline still runs. Tests use fixtures, not the network.
"""

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..models import EmailSecuritySignal

DOH_ENDPOINT = "https://dns.google/resolve"


def _lookup_txt_doh(name: str, timeout: int = 15) -> list[str]:
    """Resolve TXT records over DNS-over-HTTPS (JSON API)."""
    url = DOH_ENDPOINT + "?" + urlencode({"name": name, "type": "TXT"})
    req = Request(url, headers={"accept": "application/dns-json"})
    with urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode())
    out: list[str] = []
    for ans in data.get("Answer", []):
        if ans.get("type") == 16:  # TXT
            out.append((ans.get("data") or "").strip('"'))
    return out


def _lookup_txt_native(name: str) -> list[str]:
    """Resolve TXT records via dnspython (UDP/53)."""
    import dns.resolver  # type: ignore

    try:
        answers = dns.resolver.resolve(name, "TXT")
    except Exception:
        return []
    out: list[str] = []
    for rdata in answers:
        try:
            parts = [b.decode() if isinstance(b, bytes) else str(b) for b in rdata.strings]
            out.append("".join(parts))
        except Exception:
            out.append(str(rdata).strip('"'))
    return out


def _lookup_txt(name: str, resolver: str = "auto") -> list[str]:
    """Return TXT record strings for a name, or [] on a resolved-but-empty name.

    resolver: "doh" | "native" | "auto" (DoH first, native fallback).
    Raises RuntimeError only if no resolver is usable at all.
    """
    if resolver in ("doh", "auto"):
        try:
            return _lookup_txt_doh(name)
        except Exception:
            if resolver == "doh":
                raise RuntimeError("DoH lookup failed")
    try:
        return _lookup_txt_native(name)
    except Exception as exc:
        raise RuntimeError(f"no DNS resolver available ({exc})")


def evaluate_records(spf_txt: list[str], dmarc_txt: list[str]) -> EmailSecuritySignal:
    """Grade SPF/DMARC records. Pure function -- unit-testable without DNS."""
    has_spf = any(t.lower().startswith("v=spf1") for t in spf_txt)

    dmarc_policy = None
    has_dmarc = False
    for t in dmarc_txt:
        low = t.lower().replace(" ", "")
        if low.startswith("v=dmarc1"):
            has_dmarc = True
            for token in low.split(";"):
                if token.startswith("p="):
                    dmarc_policy = token[2:] or None
            break

    findings: list[str] = []
    if not has_spf:
        findings.append("No SPF record")
    if not has_dmarc:
        findings.append("No DMARC record")
    elif dmarc_policy in (None, "none"):
        findings.append("DMARC present but policy is 'none' (monitor only, not enforced)")

    # Grade: strong requires SPF + enforced DMARC; weak = missing DMARC or no enforcement.
    if not has_dmarc or dmarc_policy in (None, "none"):
        weakness = "weak"
    elif has_spf and dmarc_policy in ("quarantine", "reject"):
        weakness = "strong"
    else:
        weakness = "partial"

    return EmailSecuritySignal(
        weakness=weakness,
        has_spf=has_spf,
        has_dmarc=has_dmarc,
        dmarc_policy=dmarc_policy,
        findings=findings,
    )


def check_domain(domain: str | None, resolver: str = "auto") -> EmailSecuritySignal:
    if not domain:
        return EmailSecuritySignal(weakness="unknown", findings=["No domain to check"])
    domain = domain.strip().lower().replace("https://", "").replace("http://", "").strip("/")
    try:
        spf_txt = _lookup_txt(domain, resolver)
        dmarc_txt = _lookup_txt(f"_dmarc.{domain}", resolver)
    except RuntimeError as exc:
        return EmailSecuritySignal(weakness="unknown", findings=[f"DNS unavailable: {exc}"])
    return evaluate_records(spf_txt, dmarc_txt)
