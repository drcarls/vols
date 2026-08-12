"""Registry harvest tests — SNI catalog, CSV-export parsing, discovery (offline)."""

from presales_scout.collectors import registry
from presales_scout.collectors.registry import sni_catalog
from presales_scout.collectors.registry.csv_export import load_rows
from presales_scout.collectors.registry.fixture import _DEFAULT


def test_sector_aliases_resolve():
    assert sni_catalog.resolve_sector("energy") == "Energy"
    assert sni_catalog.resolve_sector("Transport") == "Transport"
    assert sni_catalog.resolve_sector("el") == "Energy"
    assert sni_catalog.resolve_sector("nonsense") is None


def test_codes_for_sectors_dedup_and_content():
    codes = sni_catalog.codes_for_sectors(["energy", "transport"])
    assert "35110" in codes and "49410" in codes
    assert len(codes) == len(set(codes))  # deduped
    # a canonical name works the same as an alias
    assert sni_catalog.codes_for_sectors(["Energy"]) == sni_catalog.SECTOR_SNI["Energy"]


def test_csv_export_parses_swedish_headers():
    rows = load_rows(_DEFAULT)
    names = {c.name for c in rows}
    assert "Nyköping Energi AB" in names
    nyk = next(c for c in rows if c.name == "Nyköping Energi AB")
    assert nyk.sni_code == "35300"
    assert nyk.employees == 180
    assert nyk.domain == "nykopingenergi.se"          # https:// and www. stripped
    assert nyk.turnover_eur and nyk.turnover_eur > 10_000_000  # 620000 tkr -> EUR


def test_discover_universe_filters_and_dedupes():
    backend = registry.FixtureBackend()
    got = registry.discover_universe(backend, ["energy", "transport"], min_employees=50)
    names = {c.name for c in got}
    # in-scope energy + transport kept
    assert "Kustkraft Sverige AB" in names
    assert "Nordfrakt Logistik AB" in names
    # below threshold dropped (12 staff, ~EUR 3.4M turnover)
    assert "Lilla Byns Elhandel AB" not in names
    # wrong sector never queried (food)
    assert "Grönsakshallen Färsk AB" not in names
    # taxi SNI 49320 is deliberately not in the transport catalog
    assert "Minitaxi i Staden AB" not in names
    # every kept company is genuinely in a target sector
    from presales_scout.collectors import nis2
    assert all(nis2.qualify(c).sector in ("Energy", "Transport") for c in got)


def test_discover_strict_size_drops_unknown():
    # a company in a covered sector with no size data is 'likely_in_scope'
    from presales_scout.models import Company

    class OneUnknown:
        def discover(self, sni_codes, *, min_employees=50, country="SE", limit=None):
            return [Company(name="Mystery Energi AB", sni_code="35110")]  # no size

    lenient = registry.discover_universe(OneUnknown(), ["energy"], include_likely=True)
    strict = registry.discover_universe(OneUnknown(), ["energy"], include_likely=False)
    assert len(lenient) == 1 and len(strict) == 0
