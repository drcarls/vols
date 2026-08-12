from __future__ import annotations

"""RegistryBackend — the pluggable candidate-universe source.

Same pattern as CisoBackend: one narrow protocol, several interchangeable
implementations (live Roaring API, a bring-your-own CSV export, an offline
fixture). Every backend returns the same `Company` shape the rest of the
pipeline already consumes, so swapping the source changes nothing downstream —
this is the seam the README always pointed at.
"""

from typing import Protocol

from ...models import Company


class RegistryBackend(Protocol):
    def discover(
        self,
        sni_codes: list[str],
        *,
        min_employees: int = 50,
        country: str = "SE",
        limit: int | None = None,
    ) -> list[Company]:
        """Return companies in the given SNI industries at or above the size floor.

        Backends should populate name + org_number + sni_code + a size field
        (employees and/or turnover) and, where available, domain. Size filtering
        is best-effort at the source; `discover_universe` re-checks NIS2 scope so
        a loose backend never leaks below-threshold rows downstream.
        """
        ...
