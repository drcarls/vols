from __future__ import annotations

"""NIS2 scope qualification under the Swedish Cybersecurity Act.

Cybersakerhetslagen (SFS 2025:1506) entered into force 15 Jan 2026. It
covers 18 sectors and applies to entities with >= 50 employees OR annual
turnover / balance-sheet total >= EUR 10 million. Some digital-infrastructure
and trust-service providers are in scope regardless of size.

We qualify from public company fields (SNI industry code + size). This is
a screening heuristic, not a legal determination -- final scope always
needs a human read of the entity's actual activities.
"""

from ..models import Company, Nis2Verdict

SIZE_THRESHOLD_EMPLOYEES = 50
SIZE_THRESHOLD_EUR = 10_000_000

# NIS2 sectors mapped to leading SNI (Swedish SNI ~ EU NACE) code prefixes.
# Not exhaustive -- covers the sectors most relevant to Cyber Defencely's
# initial focus (energy, transport) plus the other clearly-mappable ones.
SNI_SECTOR_PREFIXES: list[tuple[str, str]] = [
    ("35", "Energy"),
    ("36", "Drinking water"),
    ("37", "Waste water"),
    ("38", "Waste management"),
    ("49", "Transport"),
    ("50", "Transport"),
    ("51", "Transport"),
    ("52", "Transport"),
    ("53", "Postal and courier"),
    ("61", "Digital infrastructure"),
    ("62", "ICT service management"),
    ("63", "Digital infrastructure"),
    ("64", "Banking / financial"),
    ("65", "Financial market infrastructure"),
    ("66", "Financial market infrastructure"),
    ("86", "Health"),
    ("21", "Manufacturing (pharma)"),
    ("20", "Chemicals"),
    ("10", "Food"),
    ("11", "Food"),
    ("84", "Public administration"),
]

# Sectors treated as in scope regardless of size (simplified).
SIZE_EXEMPT_SECTORS = {"Digital infrastructure"}


def match_sector(sni_code: str | None) -> str | None:
    if not sni_code:
        return None
    code = sni_code.strip().replace(".", "").replace(" ", "")
    for prefix, sector in SNI_SECTOR_PREFIXES:
        if code.startswith(prefix):
            return sector
    return None


def meets_size_threshold(company: Company) -> bool | None:
    known = False
    if company.employees is not None:
        known = True
        if company.employees >= SIZE_THRESHOLD_EMPLOYEES:
            return True
    for value in (company.turnover_eur, company.balance_sheet_eur):
        if value is not None:
            known = True
            if value >= SIZE_THRESHOLD_EUR:
                return True
    return False if known else None


def qualify(company: Company) -> Nis2Verdict:
    sector = match_sector(company.sni_code)
    sector_in_scope = sector is not None
    reasons: list[str] = []

    if not sector_in_scope:
        reasons.append(
            f"SNI {company.sni_code or '(missing)'} does not map to a NIS2 sector"
        )
        return Nis2Verdict(
            verdict="out_of_scope" if company.sni_code else "unknown",
            sector=None,
            sector_in_scope=False,
            meets_size_threshold=None,
            reasons=reasons,
        )

    reasons.append(f"In NIS2 sector: {sector} (SNI {company.sni_code})")

    if sector in SIZE_EXEMPT_SECTORS:
        reasons.append("Sector is in scope regardless of size")
        return Nis2Verdict(
            verdict="in_scope",
            sector=sector,
            sector_in_scope=True,
            meets_size_threshold=True,
            reasons=reasons,
        )

    size_ok = meets_size_threshold(company)
    if size_ok is True:
        reasons.append(
            f"Meets size threshold (>= {SIZE_THRESHOLD_EMPLOYEES} employees "
            f"or EUR {SIZE_THRESHOLD_EUR:,} turnover/balance sheet)"
        )
        verdict = "in_scope"
    elif size_ok is False:
        reasons.append("Below the size threshold on the data we have")
        verdict = "out_of_scope"
    else:
        reasons.append("Size unknown -- in a covered sector but headcount/turnover missing")
        verdict = "likely_in_scope"

    return Nis2Verdict(
        verdict=verdict,
        sector=sector,
        sector_in_scope=True,
        meets_size_threshold=size_ok,
        reasons=reasons,
    )
