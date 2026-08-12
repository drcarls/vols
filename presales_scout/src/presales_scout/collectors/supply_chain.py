from __future__ import annotations

"""Passive digital supply-chain mapping.

Identifies a company's external suppliers/service providers from public
signals only:
  - email provider / email-security gateway (MX records)
  - DNS provider (NS records)
  - cloud / CDN / hosting and every third-party script running in the
    homepage (parsed from HTML resource hosts + the CSP allow-list header)

Each supplier is classified (category, criticality, whether it executes in
the page = data access). This maps directly to NIS2 Art. 21(2)(d)
supply-chain security: the entity is accountable for these providers.
"""

import re
from urllib.request import Request, urlopen

from . import _doh

# host substring -> (vendor, category, criticality, runs_in_page)
KNOWN: list[tuple[str, tuple[str, str, str, bool]]] = [
    # email
    ("protection.outlook", ("Microsoft 365 (Exchange Online)", "email", "high", False)),
    ("outlook.com", ("Microsoft 365", "email", "high", False)),
    ("pphosted", ("Proofpoint", "email_security", "high", False)),
    ("proofpoint", ("Proofpoint", "email_security", "high", False)),
    ("mimecast", ("Mimecast", "email_security", "high", False)),
    ("messagelabs", ("Broadcom/Symantec email", "email_security", "high", False)),
    ("mailgun", ("Mailgun", "email", "medium", False)),
    ("sendgrid", ("Twilio SendGrid", "email", "medium", False)),
    ("google.com.", ("Google Workspace", "email", "high", False)),  # MX aspmx.l.google.com.
    ("aspmx", ("Google Workspace", "email", "high", False)),
    # dns / cdn / cloud
    ("cloudflare", ("Cloudflare", "cdn_dns", "high", False)),
    ("akamai", ("Akamai", "cdn", "high", False)),
    ("fastly", ("Fastly", "cdn", "high", False)),
    ("azureedge", ("Azure CDN", "cloud_cdn", "high", False)),
    ("cloudfront", ("AWS CloudFront", "cloud_cdn", "high", False)),
    ("amazonaws", ("AWS", "cloud", "high", False)),
    ("azurewebsites", ("Microsoft Azure", "cloud", "high", False)),
    ("windows.net", ("Microsoft Azure", "cloud", "high", False)),
    ("googleapis", ("Google APIs/Cloud", "cloud", "medium", True)),
    ("dipcon", ("Dipcon (DNS/hosting)", "dns", "high", False)),
    ("foundationdns", ("Cloudflare Foundation DNS", "cdn_dns", "high", False)),
    # tag managers / dtm (can inject anything -> high)
    ("googletagmanager", ("Google Tag Manager", "tag_manager", "high", True)),
    ("adobedtm", ("Adobe Tag Manager", "tag_manager", "high", True)),
    ("assets.adobedtm", ("Adobe Tag Manager", "tag_manager", "high", True)),
    # analytics
    ("google-analytics", ("Google Analytics", "analytics", "medium", True)),
    ("omtrdc.net", ("Adobe Analytics", "analytics", "medium", True)),
    # advertising / pixels
    ("doubleclick", ("Google Ads", "advertising", "medium", True)),
    ("googlesyndication", ("Google Ads", "advertising", "medium", True)),
    ("googleads", ("Google Ads", "advertising", "medium", True)),
    ("bat.bing", ("Microsoft Ads", "advertising", "medium", True)),
    ("connect.facebook", ("Meta Pixel", "advertising", "medium", True)),
    ("analytics.tiktok", ("TikTok Pixel", "advertising", "medium", True)),
    ("teads", ("Teads", "advertising", "medium", True)),
    ("tradedoubler", ("Tradedoubler", "advertising", "medium", True)),
    # personalization / AB testing / session replay (see user data -> high)
    ("kameleoon", ("Kameleoon A/B testing", "ab_testing", "high", True)),
    ("experimentation.dev", ("Experimentation platform", "ab_testing", "high", True)),
    ("mouseflow", ("Mouseflow session replay", "session_replay", "high", True)),
    ("scene7", ("Adobe Scene7 media", "media_cdn", "medium", False)),
    # consent
    ("cookielaw", ("OneTrust consent", "consent_cmp", "medium", True)),
    ("onetrust", ("OneTrust consent", "consent_cmp", "medium", True)),
    # chat / AI
    ("ebiai", ("ebiAI chatbot", "ai_chat", "high", True)),
    # captcha / security
    ("challenges.cloudflare", ("Cloudflare Turnstile", "security_captcha", "medium", True)),
    ("recaptcha", ("Google reCAPTCHA", "security_captcha", "medium", True)),
    ("gstatic", ("Google static/reCAPTCHA", "cdn_js", "low", True)),
    # reviews / partners
    ("trustpilot", ("Trustpilot", "reviews", "low", True)),
    ("sembo.travel", ("Sembo partner API", "partner_saas", "medium", True)),
    ("adobe.com", ("Adobe Document Services", "saas", "medium", True)),
    # generic public JS CDNs
    ("jsdelivr", ("jsDelivr CDN", "cdn_js", "medium", True)),
    ("unpkg", ("unpkg CDN", "cdn_js", "medium", True)),
    ("cdnjs", ("cdnjs", "cdn_js", "medium", True)),
]

_HOST_RE = re.compile(r"https?://([a-z0-9.\-]+)", re.I)

# XML/RDF namespaces and public-suffix fragments that are not real suppliers
_IGNORE = {"schema.org", "w3.org", "purl.org", "example.com", "example.org",
           "co.uk", "org.uk", "com.au", "gmpg.org", "ogp.me"}
_MULTIPART_TLDS = ("co.uk", "org.uk", "com.au", "co.jp")


def _registrable(host: str) -> str:
    parts = host.strip(".").split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in _MULTIPART_TLDS:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def _brand(host: str) -> str:
    reg = _registrable(host)
    return reg.split(".")[0]


def _classify(host: str):
    low = host.lower()
    for key, info in KNOWN:
        if key in low:
            return info
    return None


def _fetch_html_and_csp(domain: str, timeout: int = 20):
    url = f"https://{domain.strip().lower()}"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; presales-scout/0.1)"})
    with urlopen(req, timeout=timeout) as resp:
        csp = resp.headers.get("content-security-policy", "")
        body = resp.read(500_000).decode("utf-8", "replace")
    return body, csp


def map_suppliers(domain: str) -> dict:
    d = domain.strip().lower()
    own_brand = _brand(d)
    suppliers: dict[str, dict] = {}   # keyed by (vendor) to dedupe

    def add(host, layer):
        reg = _registrable(host)
        info = _classify(host)
        if info is None:
            # drop own-brand ccTLDs and namespace/noise hosts
            if _brand(host) == own_brand or reg in _IGNORE or "." not in reg:
                return
        if info:
            vendor, cat, crit, in_page = info
        else:
            vendor, cat, crit, in_page = (reg, "third_party", "low", layer == "web_script")
        key = vendor
        if key not in suppliers:
            suppliers[key] = dict(vendor=vendor, host=reg, layer=layer, category=cat,
                                  criticality=crit, data_access=in_page)

    # email + DNS providers
    for mx in _doh.resolve(d, "MX"):
        host = mx.split()[-1] if mx else mx
        add(host, "email")
    for ns in _doh.resolve(d, "NS"):
        add(ns, "dns")

    # web third parties from HTML resource hosts + CSP allow-list
    try:
        body, csp = _fetch_html_and_csp(d)
        hosts = set(_HOST_RE.findall(body)) | set(_HOST_RE.findall(csp))
        for h in hosts:
            if h.endswith(d) or _registrable(h) == _registrable(d):
                continue  # first-party
            add(h, "web_script")
    except Exception:
        pass

    sup = list(suppliers.values())
    # risk finding for the context map
    in_page = [s for s in sup if s["data_access"]]
    high = [s for s in sup if s["criticality"] == "high"]
    findings: list[tuple[str, str]] = []
    if sup:
        ev = (f"{len(sup)} external suppliers mapped "
              f"({len(in_page)} run in-page with data access, {len(high)} high-criticality)")
        findings.append(("SUPPLY_UNMANAGED", ev))
    return {"suppliers": sup, "findings": findings}


def scan(domain: str) -> list[tuple[str, str]]:
    """Collector interface: return just the finding codes for the context map."""
    return map_suppliers(domain)["findings"]
