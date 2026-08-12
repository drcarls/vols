from __future__ import annotations

"""Live candidate-universe backend: SEC EDGAR company listings by SIC.

Stage 1 in v1 is a hand-supplied CSV. This backend builds that universe
automatically: for each regulated-data sector we care about, it queries
EDGAR's public ``browse-edgar`` company listing by SIC code and parses the
results into the same ``Company`` shape the pipeline already consumes -- so
nothing downstream changes.

EDGAR covers SEC registrants (public companies and funds). It's the free,
public, no-key analogue of the allabolag/Bolagsverket backend the NIS2 tool
planned. SIC codes are crosswalked to the NAICS-style codes the regulated
qualifier understands, so a health-services registrant (SIC 80xx) lands as
NAICS 62 -> PHI/HIPAA automatically.

The pure parser (``parse_listing``) is unit-tested against a saved fixture;
the network fetch degrades to a bundled fixture when EDGAR is unreachable.
Be a good citizen: EDGAR asks for a descriptive User-Agent and modest rates.
"""

import html
import os
import re
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..config import fixtures_dir
from ..models import Company

EDGAR_URL = "https://www.sec.gov/cgi-bin/browse-edgar"

# SEC's fair-access policy requires a descriptive User-Agent naming a real
# contact. Set EDGAR_USER_AGENT="Your Name your.email@example.com" before a
# live run; without it EDGAR will 403 aggressive/anonymous traffic and the
# backend falls back to any bundled fixture.
_DEFAULT_UA = "questa-scout/0.1 pre-sales research (set EDGAR_USER_AGENT with a contact email)"


def user_agent() -> str:
    return os.environ.get("EDGAR_USER_AGENT", _DEFAULT_UA)

# Sector key -> list of (SIC code, NAICS-equivalent the qualifier understands).
# The NAICS code only needs to prefix-match one of regulated.NAICS_SECTORS.
SECTOR_SIC: dict[str, list[tuple[str, str]]] = {
    "health": [
        ("8000", "621"),   # health services
        ("8011", "621"),   # offices of physicians
        ("8060", "622"),   # hospitals
        ("8071", "6215"),  # medical laboratories
    ],
    "pharma": [
        ("2834", "3254"),  # pharmaceutical preparations
        ("2836", "3254"),  # biological products
    ],
    "finance": [
        ("6022", "522"),   # state commercial banks
        ("6035", "522"),   # savings institutions
        ("6199", "522"),   # finance services
        ("6211", "523"),   # security brokers & dealers
    ],
    "insurance": [
        ("6311", "524"),   # life insurance
        ("6411", "524"),   # insurance agents & brokers
    ],
    "legal": [
        ("8111", "5411"),  # legal services
    ],
    "software": [
        ("7372", "5112"),  # prepackaged software (SaaS)
    ],
    "dataproc": [
        ("7374", "5182"),  # computer processing & data prep
    ],
}

# Regex for one company row in the EDGAR HTML listing:
#   <a ...CIK=..>0001234567</a></td><td>COMPANY NAME</td><td>STATE</td>
_ROW = re.compile(
    r'>(\d{10})</a></td>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>',
    re.S,
)
_TAGS = re.compile(r"<[^>]+>")


def _clean(text: str) -> str:
    return html.unescape(_TAGS.sub("", text or "")).strip()


def parse_listing(page_html: str) -> list[dict]:
    """Parse an EDGAR company listing into [{cik, name, state}]. Pure."""
    out: list[dict] = []
    for cik, name, state in _ROW.findall(page_html or ""):
        name_c = _clean(name)
        if not name_c:
            continue
        out.append({"cik": cik, "name": name_c, "state": _clean(state) or None})
    return out


def _fixture_html(sic: str) -> str | None:
    path = fixtures_dir() / "edgar" / f"sic-{sic}.html"
    if path.exists():
        return path.read_text(encoding="latin-1")
    return None


def fetch_sic_html(sic: str, count: int = 100, timeout: int = 25, retries: int = 2) -> str:
    """Fetch the EDGAR company listing HTML for a SIC code (network).

    Retries with backoff on 403/429 (SEC rate-limiting).
    """
    params = {
        "action": "getcompany",
        "SIC": sic,
        "type": "10-K",
        "dateb": "",
        "owner": "include",
        "count": str(count),
    }
    url = EDGAR_URL + "?" + urlencode(params)
    last: Exception | None = None
    for attempt in range(retries + 1):
        req = Request(url, headers={"User-Agent": user_agent(), "Accept-Encoding": "identity"})
        try:
            with urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("latin-1", errors="ignore")
        except HTTPError as exc:
            last = exc
            if exc.code in (403, 429, 500, 502, 503) and attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise
    raise last if last else RuntimeError("fetch failed")


def build_universe(
    sectors: list[str],
    *,
    limit_per_sic: int = 40,
    offline: bool = False,
    polite_delay: float = 0.3,
) -> list[Company]:
    """Build a de-duplicated candidate list across the requested sectors.

    offline=True (or a failed fetch) falls back to any bundled fixture for
    that SIC, so the command still yields something with no network.
    """
    companies: list[Company] = []
    seen: set[str] = set()

    for sector in sectors:
        pairs = SECTOR_SIC.get(sector)
        if not pairs:
            continue
        for sic, naics in pairs:
            page = None
            if not offline:
                try:
                    page = fetch_sic_html(sic, count=limit_per_sic)
                    if polite_delay:
                        time.sleep(polite_delay)
                except Exception:
                    page = None
            if page is None:
                page = _fixture_html(sic)
            if not page:
                continue
            for rec in parse_listing(page)[:limit_per_sic]:
                key = rec["name"].lower().strip()
                if key in seen:
                    continue
                seen.add(key)
                companies.append(
                    Company(
                        name=rec["name"],
                        naics_code=naics,
                        state=rec.get("state"),
                        country="US",
                    )
                )
    return companies
