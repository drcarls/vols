from __future__ import annotations

"""End-to-end prospecting pipeline.

Stage 1 (candidate universe) is fed from a CSV in v1 -- a live
allabolag/Bolagsverket backend can later populate the same Company shape.
Stages 2-4 (NIS2 qualify, email hygiene, CISO detection) run per company,
then everything is scored and ranked.
"""

import csv
from pathlib import Path
from typing import Iterable, Optional

from .collectors import email_security, nis2
from .collectors.ciso import detect_ciso
from .collectors.ciso.base import CisoBackend
from .models import Company, ProspectReport
from .scoring import score


def load_candidates(csv_path: str | Path) -> list[Company]:
    companies: list[Company] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            companies.append(
                Company(
                    name=(row.get("name") or "").strip(),
                    domain=(row.get("domain") or "").strip() or None,
                    org_number=(row.get("org_number") or "").strip() or None,
                    sni_code=(row.get("sni_code") or "").strip() or None,
                    employees=_int(row.get("employees")),
                    turnover_eur=_float(row.get("turnover_eur")),
                    balance_sheet_eur=_float(row.get("balance_sheet_eur")),
                    country=(row.get("country") or "SE").strip() or "SE",
                )
            )
    return [c for c in companies if c.name]


def _int(v: Optional[str]) -> Optional[int]:
    try:
        return int(float(v)) if v not in (None, "") else None
    except (ValueError, TypeError):
        return None


def _float(v: Optional[str]) -> Optional[float]:
    try:
        return float(v) if v not in (None, "") else None
    except (ValueError, TypeError):
        return None


def analyze(
    company: Company,
    ciso_backend: CisoBackend,
    *,
    check_email: bool = True,
) -> ProspectReport:
    verdict = nis2.qualify(company)
    email = (
        email_security.check_domain(company.domain)
        if check_email
        else email_security.EmailSecuritySignal(weakness="unknown", findings=["email check skipped"])
    )
    ciso = detect_ciso(company, ciso_backend)
    return score(company, verdict, email, ciso)


def run(
    companies: Iterable[Company],
    ciso_backend: CisoBackend,
    *,
    check_email: bool = True,
) -> list[ProspectReport]:
    reports = [analyze(c, ciso_backend, check_email=check_email) for c in companies]
    reports.sort(key=lambda r: r.fit_score, reverse=True)
    return reports


def write_csv(reports: list[ProspectReport], out_path: str | Path) -> None:
    rows = [r.to_row() for r in reports]
    if not rows:
        return
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
