from __future__ import annotations

"""End-to-end prospecting pipeline.

Stage 1 (candidate universe) is fed from a CSV in v1 -- a live data.gov /
SEC EDGAR / state-registry backend can later populate the same Company shape.
Stages 2-4 (regulated-data qualify, AI-adoption, governance detection) run
per company, then everything is scored, routed, and ranked.
"""

import csv
from pathlib import Path
from typing import Iterable, Optional

from .collectors import ai_adoption, ai_governance, regulated
from .collectors.serp.base import SerpBackend
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
                    naics_code=(row.get("naics_code") or "").strip() or None,
                    employees=_int(row.get("employees")),
                    revenue_usd=_float(row.get("revenue_usd")),
                    state=(row.get("state") or "").strip() or None,
                    country=(row.get("country") or "US").strip() or "US",
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
    backend: SerpBackend,
    *,
    check_web: bool = True,
) -> ProspectReport:
    verdict = regulated.qualify(company)
    adoption = ai_adoption.detect_adoption(company, backend, check_web=check_web)
    governance = ai_governance.detect_governance(company, backend)
    return score(company, verdict, adoption, governance)


def run(
    companies: Iterable[Company],
    backend: SerpBackend,
    *,
    check_web: bool = True,
) -> list[ProspectReport]:
    reports = [analyze(c, backend, check_web=check_web) for c in companies]
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


def write_candidates_csv(companies: list[Company], out_path: str | Path) -> None:
    """Write Company objects out in the Stage-1 candidates CSV format, so a
    universe built from EDGAR can be reviewed/edited before `discover`."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["name", "domain", "naics_code", "employees", "revenue_usd", "state", "country"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for c in companies:
            writer.writerow({
                "name": c.name,
                "domain": c.domain or "",
                "naics_code": c.naics_code or "",
                "employees": c.employees if c.employees is not None else "",
                "revenue_usd": c.revenue_usd if c.revenue_usd is not None else "",
                "state": c.state or "",
                "country": c.country or "US",
            })


def write_findings_csv(reports: list[ProspectReport], out_path: str | Path) -> None:
    """Write the per-finding view (one row per mapped signal)."""
    from .context_map import derive_findings

    rows = []
    for r in reports:
        for f in derive_findings(r):
            row = f.to_row()
            row["fit_score"] = round(r.fit_score, 1)
            rows.append(row)
    if not rows:
        return
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
