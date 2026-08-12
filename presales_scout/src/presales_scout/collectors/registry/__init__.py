"""Registry backends — auto-generate the candidate universe from SNI + size.

The seam the README always pointed at: instead of hand-assembling a candidate
CSV, harvest "every Swedish energy & transport firm >= 50 staff" from a company
registry. Pluggable, same `Company` shape downstream:

    RoaringBackend      live Roaring Company Prospecting API (key-gated)
    CsvExportBackend    a downloaded allabolag/Bolagsverket/Roaring CSV export
    FixtureBackend      bundled offline sample

    discover_universe(backend, ["energy", "transport"], min_employees=50)
        -> list[Company]  (NIS2-qualified, deduped)
"""

from .base import RegistryBackend
from .csv_export import CsvExportBackend, load_rows
from .fixture import FixtureBackend
from .roaring import RegistryAuthError, RoaringBackend
from .discover import discover_universe
from .sni_catalog import SECTOR_SNI, codes_for_sectors, resolve_sector

__all__ = [
    "RegistryBackend",
    "CsvExportBackend",
    "load_rows",
    "FixtureBackend",
    "RoaringBackend",
    "RegistryAuthError",
    "discover_universe",
    "SECTOR_SNI",
    "codes_for_sectors",
    "resolve_sector",
]
