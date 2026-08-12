from __future__ import annotations

"""Clay (and any HTTP-column tool) enrichment endpoint.

Clay orchestrates outbound by calling data providers per row and waterfalling
the results. This module is *our* provider: Clay sends a domain, we return the
regulatory-risk signal bundle no generic vendor sells — NIS2 scope, email
hygiene, CISO gap + hiring trigger, passive attack surface, supplier exposure —
already context-mapped to the NIS2/ISO obligation and the Cyber Defencely
service that closes it.

Two entry points:

  enrich_domain(payload) -> dict   the pure function; unit-testable, no server.
  serve(port)                      a zero-dependency stdlib HTTP wrapper.

--------------------------------------------------------------------------- #
JSON contract (what Clay's HTTP-enrichment column sends and receives)
--------------------------------------------------------------------------- #

REQUEST  (POST application/json)
  {
    "domain": "goteborgenergi.se",   # required
    "name": "Göteborg Energi AB",    # optional; improves the CISO query
    "sni_code": "35110",             # optional; drives NIS2 sector match
    "employees": 1150,               # optional \
    "turnover_eur": 400000000,       # optional  } drive the NIS2 size test
    "org_number": "556362-6794"      # optional /
  }

RESPONSE (200 application/json) — every field is flat/scalar so it maps
straight onto Clay columns and filters:
  {
    "domain": "...", "company": "...",
    "nis2_in_scope": true, "nis2_verdict": "in_scope", "nis2_sector": "Energy",
    "email_weakness": "weak", "dmarc_policy": "none",
    "ciso_status": "none_found", "ciso_confidence": 0.7,
    "ciso_verify_recommended": true, "ciso_name": "", "ciso_title": "",
    "fit_score": 100.0,
    "top_finding": "No DMARC record",
    "top_finding_nis2": "Art. 21(2)(g) basic cyber hygiene",
    "top_finding_service": "Rapid Cybersecurity Assessment (email-security quick win)",
    "finding_count": 9, "max_severity": "high",
    "talking_point": "…one-line opener grounded on the evidence…",
    "findings": [ {full Finding.to_row() dicts, severity-sorted} ],
    "signals_ran": ["nis2","email","ciso","attack_surface","supplier"]
  }

Errors return {"error": "...", "domain": "..."} with a 4xx/5xx status; Clay
treats that row as unenriched and waterfalls to the next provider.

Point Clay's HTTP-enrichment column (or a webhook on a "hiring a CISO" trigger)
at POST /enrich. No auth is added here — deploy behind whatever gateway/token
your infra uses; never expose it open to the internet.
"""

import json
import os
from typing import Optional
from urllib.parse import urlparse

from ..models import Company
from ..collectors import email_security, nis2, passive
from ..collectors.ciso import BrightDataSerpBackend, FixtureBackend, detect_ciso
from ..collectors.ciso.base import CisoBackend
from ..config import brightdata_token
from ..context_engine import enrich as context_enrich


def _select_backend() -> CisoBackend:
    """Live Bright Data SERP when a token is present; fixture backend otherwise.

    The fixture backend only knows the demo companies — a live endpoint needs
    BRIGHTDATA_API_TOKEN set to resolve arbitrary domains. We fall back rather
    than fail so the endpoint still returns the (token-free) NIS2 + email +
    passive signals.
    """
    token = brightdata_token()
    if token:
        return BrightDataSerpBackend(token, zone=os.environ.get("BRIGHTDATA_SERP_ZONE", "serp"))
    return FixtureBackend()


def _clean_domain(raw: str) -> str:
    """Accept a bare domain or a full URL; return the hostname, no www."""
    raw = (raw or "").strip()
    if "//" in raw:
        raw = urlparse(raw).netloc or urlparse("//" + raw).netloc
    raw = raw.split("/")[0].strip().lower()
    return raw[4:] if raw.startswith("www.") else raw


def enrich_domain(payload: dict, *, backend: Optional[CisoBackend] = None,
                  run_network: bool = True) -> dict:
    """Run the full signal stack for one company and flatten it for Clay.

    `payload` follows the REQUEST contract above. `backend` is injectable for
    tests; `run_network=False` skips the live passive collectors (email/NIS2/
    CISO still run) for a fast, offline-friendly response.
    """
    domain = _clean_domain(payload.get("domain", ""))
    if not domain:
        raise ValueError("domain is required")

    company = Company(
        name=payload.get("name") or domain,
        domain=domain,
        org_number=payload.get("org_number"),
        sni_code=payload.get("sni_code"),
        employees=payload.get("employees"),
        turnover_eur=payload.get("turnover_eur"),
        balance_sheet_eur=payload.get("balance_sheet_eur"),
    )

    # --- core signals (email + NIS2 need no API key) ---
    verdict = nis2.qualify(company)
    email = email_security.check_domain(domain) if run_network else \
        email_security.EmailSecuritySignal(weakness="unknown", findings=["network disabled"])
    ciso = detect_ciso(company, backend or _select_backend())

    # --- passive attack-surface + supplier findings, context-mapped ---
    pairs = passive.collect(
        company, email_sig=email, ciso_status=ciso.status,
        nis2_verdict=verdict.verdict, run_network=run_network,
    )
    findings = []
    seen: set[str] = set()
    for code, evidence in pairs:
        if code in seen:
            continue
        seen.add(code)
        f = context_enrich(code, evidence, company)
        if f:
            findings.append(f)
    findings.sort(key=lambda f: f.severity_score, reverse=True)

    leader = next((p for p in ciso.people if p.role_tier == "leader"), None)
    top = findings[0] if findings else None

    out = {
        "domain": domain,
        "company": company.name,
        "nis2_in_scope": verdict.verdict in ("in_scope", "likely_in_scope"),
        "nis2_verdict": verdict.verdict,
        "nis2_sector": verdict.sector or "",
        "email_weakness": email.weakness,
        "dmarc_policy": email.dmarc_policy or "",
        "ciso_status": ciso.status,
        "ciso_confidence": round(ciso.confidence, 2),
        "ciso_verify_recommended": ciso.verify_recommended,
        "ciso_name": leader.name if leader else "",
        "ciso_title": leader.title if leader else "",
        "top_finding": top.title if top else "",
        "top_finding_nis2": top.nis2_measure if top else "",
        "top_finding_service": top.service if top else "",
        "talking_point": top.talking_point if top else "",
        "finding_count": len(findings),
        "max_severity": top.severity if top else "none",
        "findings": [f.to_row() for f in findings],
        "signals_ran": ["nis2", "email", "ciso"] + (["attack_surface", "supplier"] if run_network else []),
    }
    return out


# --------------------------------------------------------------------------- #
# Zero-dependency HTTP wrapper (stdlib). For production, drop enrich_domain into
# your framework of choice (FastAPI/Flask) — this exists so the contract is a
# runnable thing to demo, not just prose.
# --------------------------------------------------------------------------- #

def _make_handler():
    from http.server import BaseHTTPRequestHandler

    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: dict) -> None:
            data = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):  # noqa: N802 (stdlib naming)
            if self.path.rstrip("/") in ("", "/health"):
                return self._send(200, {"ok": True, "service": "presales_scout.clay"})
            return self._send(404, {"error": "not found"})

        def do_POST(self):  # noqa: N802
            if self.path.rstrip("/") != "/enrich":
                return self._send(404, {"error": "not found"})
            try:
                length = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(length) or b"{}")
            except Exception:
                return self._send(400, {"error": "invalid JSON body"})
            try:
                return self._send(200, enrich_domain(payload))
            except ValueError as e:
                return self._send(400, {"error": str(e), "domain": payload.get("domain", "")})
            except Exception as e:  # never leak a stack trace to the caller
                return self._send(500, {"error": f"enrichment failed: {e}",
                                        "domain": payload.get("domain", "")})

        def log_message(self, *_):  # quiet by default
            pass

    return Handler


def serve(port: int = 8787) -> None:
    """Run the enrichment endpoint on 0.0.0.0:<port>. POST /enrich, GET /health."""
    from http.server import HTTPServer
    server = HTTPServer(("0.0.0.0", port), _make_handler())
    print(f"presales_scout Clay endpoint on :{port}  (POST /enrich, GET /health)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":  # python -m presales_scout.integrations.clay [port]
    import sys
    serve(int(sys.argv[1]) if len(sys.argv) > 1 else 8787)
