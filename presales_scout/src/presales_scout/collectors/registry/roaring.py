from __future__ import annotations

"""Live registry backend — Roaring Company Prospecting API (key-gated).

Roaring (roaring.io) is the standard Swedish company-data API and the cleanest
live feed for "every company in these SNI industries above this size." It uses
OAuth2 client-credentials; set credentials in the environment and this backend
builds the candidate universe unattended:

    export ROARING_CLIENT_ID=...
    export ROARING_CLIENT_SECRET=...
    # optional overrides:
    export ROARING_BASE=https://api.roaring.io
    export ROARING_SEARCH_PATH=/se/company/prospect/2.0/search

Endpoint paths and response field names vary by Roaring product tier and API
version, so the response mapping is deliberately tolerant (it hunts for the
obvious keys). Treat this as the integration point to confirm against your
account's API docs — the *shape* is here; a live account wires it in. With no
credentials it raises, and the CLI falls back to the CSV/fixture backend.

The same pattern ports to allabolag or a Bolagsverket open-data feed: implement
`discover()` returning `Company` rows.
"""

import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ...models import Company


class RegistryAuthError(RuntimeError):
    pass


def _first(d: dict, *keys):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


class RoaringBackend:
    def __init__(self, client_id: str | None = None, client_secret: str | None = None,
                 *, base: str | None = None, search_path: str | None = None,
                 token_path: str = "/token"):
        self.client_id = client_id or os.environ.get("ROARING_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("ROARING_CLIENT_SECRET")
        if not (self.client_id and self.client_secret):
            raise RegistryAuthError("ROARING_CLIENT_ID / ROARING_CLIENT_SECRET not set")
        self.base = (base or os.environ.get("ROARING_BASE", "https://api.roaring.io")).rstrip("/")
        self.search_path = search_path or os.environ.get(
            "ROARING_SEARCH_PATH", "/se/company/prospect/2.0/search")
        self.token_path = token_path
        self._token: str | None = None

    # --- auth ---
    def _auth(self) -> str:
        if self._token:
            return self._token
        import base64
        cred = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        body = urlencode({"grant_type": "client_credentials"}).encode()
        req = Request(self.base + self.token_path, data=body, headers={
            "Authorization": f"Basic {cred}",
            "Content-Type": "application/x-www-form-urlencoded",
        })
        with urlopen(req, timeout=30) as r:
            tok = json.loads(r.read().decode("utf-8"))
        self._token = tok.get("access_token")
        if not self._token:
            raise RegistryAuthError(f"no access_token in token response: {tok}")
        return self._token

    # --- search ---
    def _search_page(self, sni_codes: list[str], min_employees: int, offset: int, page: int) -> dict:
        payload = {
            "companyStatus": "ACTIVE",
            "sniCode": sni_codes,
            "numberOfEmployeesFrom": min_employees,
            "offset": offset,
            "limit": page,
        }
        req = Request(self.base + self.search_path, data=json.dumps(payload).encode(),
                      headers={"Authorization": f"Bearer {self._auth()}",
                               "Content-Type": "application/json",
                               "Accept": "application/json"})
        with urlopen(req, timeout=45) as r:
            return json.loads(r.read().decode("utf-8"))

    @staticmethod
    def _to_company(rec: dict) -> Company | None:
        name = _first(rec, "companyName", "name", "legalName")
        if not name:
            return None
        emp = _first(rec, "numberOfEmployees", "employees", "numEmployees")
        turnover = _first(rec, "turnover", "revenue", "netTurnover")
        domain = _first(rec, "domain", "website", "webAddress", "homePage")
        if domain and "//" in str(domain):
            domain = str(domain).split("//", 1)[1].split("/")[0]
        if domain and str(domain).startswith("www."):
            domain = str(domain)[4:]
        try:
            emp = int(emp) if emp is not None else None
        except (TypeError, ValueError):
            emp = None
        try:
            turnover = float(turnover) if turnover is not None else None
        except (TypeError, ValueError):
            turnover = None
        return Company(
            name=str(name).strip(),
            domain=(str(domain).strip().lower() or None) if domain else None,
            org_number=_first(rec, "companyId", "organisationNumber", "orgNumber", "registrationNumber"),
            sni_code=str(_first(rec, "sniCode", "sni", "naceCode") or "").replace(".", "") or None,
            employees=emp,
            turnover_eur=turnover,
        )

    def discover(self, sni_codes: list[str], *, min_employees: int = 50,
                 country: str = "SE", limit: int | None = None) -> list[Company]:
        page = min(100, limit or 100)
        offset, out = 0, []
        while True:
            data = self._search_page(sni_codes, min_employees, offset, page)
            recs = _first(data, "hits", "companies", "results", "data") or []
            if isinstance(recs, dict):
                recs = recs.get("companies") or recs.get("items") or []
            for rec in recs:
                c = self._to_company(rec)
                if c:
                    out.append(c)
                    if limit and len(out) >= limit:
                        return out
            if len(recs) < page:
                break
            offset += page
        return out
