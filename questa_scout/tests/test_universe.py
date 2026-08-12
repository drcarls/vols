from questa_scout.universe import SECTOR_SIC, build_universe, parse_listing
from questa_scout.collectors import regulated


def _fixture_html():
    from conftest import ROOT
    return (ROOT / "fixtures" / "edgar" / "sic-8000.html").read_text(encoding="latin-1")


def test_parse_listing_extracts_name_cik_state():
    recs = parse_listing(_fixture_html())
    assert len(recs) >= 5
    first = recs[0]
    assert set(first) == {"cik", "name", "state"}
    assert first["cik"].isdigit() and len(first["cik"]) == 10
    assert first["name"]  # non-empty, tags stripped
    assert "<" not in first["name"]


def test_health_sic_maps_to_phi_hipaa():
    # SIC 8000 is configured to NAICS 621 -> the qualifier reads that as PHI.
    companies = build_universe(["health"], offline=True, limit_per_sic=5)
    assert companies, "offline fixture should yield companies"
    v = regulated.qualify(companies[0])
    assert v.data_class == "PHI"
    assert v.regime == "HIPAA"


def test_build_universe_dedups_and_sets_country():
    companies = build_universe(["health"], offline=True, limit_per_sic=10)
    names = [c.name.lower() for c in companies]
    assert len(names) == len(set(names))  # de-duplicated
    assert all(c.country == "US" for c in companies)
    assert all(c.naics_code for c in companies)


def test_sector_keys_are_known():
    assert {"health", "finance", "legal", "insurance", "software"} <= set(SECTOR_SIC)
