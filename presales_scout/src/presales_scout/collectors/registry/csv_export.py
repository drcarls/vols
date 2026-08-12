from __future__ import annotations

"""Bring-your-own-export registry backend.

The realistic first feed for a small consultancy: allabolag / Bolagsverket /
Roaring all let you export a filtered company list as CSV. This backend ingests
that export and normalises it to `Company` — tolerant of the column names each
source uses (Swedish or English, a few common spellings), so you don't have to
reshape the file by hand.

Point it at the export, ask for the SNI codes you care about, and it filters +
normalises. No API key, fully offline — the fastest path to a real 50-100 list.
"""

import csv
from pathlib import Path

from ...models import Company

# canonical field -> accepted header names (lowercased) across export sources
_COLS: dict[str, tuple[str, ...]] = {
    "name": ("name", "företagsnamn", "foretagsnamn", "company", "bolagsnamn", "juridiskt namn"),
    "org_number": ("org_number", "organisationsnummer", "orgnr", "org.nr", "orgnummer", "organization number"),
    "sni_code": ("sni_code", "sni", "snikod", "sni-kod", "bransch", "nace", "industry code"),
    "domain": ("domain", "domän", "doman", "webbplats", "website", "hemsida", "url", "web"),
    "employees": ("employees", "anställda", "anstallda", "antal anställda", "antal anstallda", "headcount"),
    "turnover_eur": ("turnover_eur", "turnover", "omsättning", "omsattning", "revenue"),
    "turnover_sek": ("turnover_sek", "omsättning tkr", "omsattning tkr", "omsättning (tkr)", "nettoomsättning"),
}

SEK_PER_EUR = 11.3  # coarse; only used when a source gives turnover in SEK/tkr


def _index(header: list[str]) -> dict[str, int]:
    lower = [h.strip().lower() for h in header]
    idx: dict[str, int] = {}
    for canon, names in _COLS.items():
        for n in names:
            if n in lower:
                idx[canon] = lower.index(n)
                break
    return idx


def _num(v: str) -> float | None:
    v = (v or "").strip().replace("\xa0", "").replace(" ", "").replace(",", ".")
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _clean_domain(v: str) -> str | None:
    v = (v or "").strip().lower()
    if not v:
        return None
    if "//" in v:
        v = v.split("//", 1)[1]
    v = v.split("/")[0]
    return v[4:] if v.startswith("www.") else v or None


def _norm_sni(v: str) -> str | None:
    v = (v or "").strip().replace(".", "").replace(" ", "")
    return v or None


def load_rows(path: str | Path) -> list[Company]:
    """Parse an export CSV into Company rows (no filtering)."""
    path = Path(path)
    with open(path, newline="", encoding="utf-8-sig") as f:
        # sniff delimiter (Swedish exports are often ';')
        sample = f.read(4096)
        f.seek(0)
        delim = ";" if sample.count(";") > sample.count(",") else ","
        reader = csv.reader(f, delimiter=delim)
        rows = list(reader)
    if not rows:
        return []
    idx = _index(rows[0])
    if "name" not in idx:
        raise ValueError(f"{path}: no recognisable company-name column in header {rows[0]}")

    companies: list[Company] = []
    for r in rows[1:]:
        def get(col: str) -> str:
            i = idx.get(col)
            return r[i] if i is not None and i < len(r) else ""

        name = get("name").strip()
        if not name:
            continue
        emp = _num(get("employees"))
        turnover = _num(get("turnover_eur"))
        if turnover is None:
            sek = _num(get("turnover_sek"))
            if sek is not None:
                # a "tkr" column is thousands of SEK; a plain SEK column is not
                sek_header = rows[0][idx["turnover_sek"]].lower() if "turnover_sek" in idx else ""
                mult = 1000 if "tkr" in sek_header else 1
                turnover = sek * mult / SEK_PER_EUR
        companies.append(Company(
            name=name,
            domain=_clean_domain(get("domain")),
            org_number=(get("org_number").strip() or None),
            sni_code=_norm_sni(get("sni_code")),
            employees=int(emp) if emp is not None else None,
            turnover_eur=turnover,
        ))
    return companies


class CsvExportBackend:
    """RegistryBackend over a downloaded registry export."""

    def __init__(self, export_path: str | Path):
        self.export_path = Path(export_path)
        self._rows: list[Company] | None = None

    def _all(self) -> list[Company]:
        if self._rows is None:
            self._rows = load_rows(self.export_path)
        return self._rows

    def discover(self, sni_codes: list[str], *, min_employees: int = 50,
                 country: str = "SE", limit: int | None = None) -> list[Company]:
        prefixes = tuple(sni_codes)
        out: list[Company] = []
        for c in self._all():
            if prefixes and not (c.sni_code and c.sni_code.startswith(prefixes)):
                continue
            # source-side size hint; discover_universe re-checks scope properly
            if c.employees is not None and c.employees < min_employees and c.turnover_eur is None:
                continue
            out.append(c)
            if limit and len(out) >= limit:
                break
        return out
