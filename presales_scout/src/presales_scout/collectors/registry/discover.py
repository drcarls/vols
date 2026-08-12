from __future__ import annotations

"""Harvest orchestrator — sectors in, NIS2-qualified candidate universe out.

Resolves the target sectors to SNI codes, asks the backend for companies in
those industries above the size floor, then re-checks NIS2 scope properly (a
backend's size filter is a hint; scope is decided here) and dedupes. The result
is a `Company` list ready to hand straight to pipeline.run — this is the step
that turns "energy & transport, >= 50 staff" into a real list without hand
assembly.
"""

from ...models import Company
from .. import nis2
from .base import RegistryBackend
from .sni_catalog import codes_for_sectors, resolve_sector


def _dedup_key(c: Company) -> str:
    return (c.org_number or "").replace("-", "").replace(" ", "") or \
        (c.domain or "").lower() or c.normalized_name()


def discover_universe(
    backend: RegistryBackend,
    sectors: list[str],
    *,
    min_employees: int = nis2.SIZE_THRESHOLD_EMPLOYEES,
    include_likely: bool = True,
    limit: int | None = None,
) -> list[Company]:
    """Return in-scope (and optionally likely-in-scope) companies for the sectors.

    `include_likely` keeps companies in a covered sector whose size is unknown
    (verdict "likely_in_scope") — worth surfacing for manual size confirmation.
    """
    canon = [resolve_sector(s) or s for s in sectors]
    codes = codes_for_sectors(canon)
    if not codes:
        return []

    raw = backend.discover(codes, min_employees=min_employees, limit=limit)

    keep_verdicts = {"in_scope"} | ({"likely_in_scope"} if include_likely else set())
    out: list[Company] = []
    seen: set[str] = set()
    for c in raw:
        if nis2.qualify(c).verdict not in keep_verdicts:
            continue
        key = _dedup_key(c)
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
        if limit and len(out) >= limit:
            break
    return out
