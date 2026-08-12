"""Contract tests for the Clay enrichment endpoint (offline, no network)."""

from conftest import fixtures_serp

from presales_scout.collectors.ciso import FixtureBackend
from presales_scout.integrations.clay import _clean_domain, enrich_domain


def _backend():
    return FixtureBackend(fixtures_serp())


def test_clean_domain_variants():
    assert _clean_domain("https://www.goteborgenergi.se/foo") == "goteborgenergi.se"
    assert _clean_domain("WWW.Example.SE ") == "example.se"
    assert _clean_domain("x.com") == "x.com"


def test_enrich_requires_domain():
    try:
        enrich_domain({}, backend=_backend(), run_network=False)
    except ValueError as e:
        assert "domain" in str(e)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError for missing domain")


def test_enrich_flat_contract():
    out = enrich_domain(
        {"domain": "energibolag.se", "name": "Energibolag AB",
         "sni_code": "35110", "employees": 500},
        backend=_backend(), run_network=False,
    )
    # every advertised key present and flat (Clay maps these onto columns)
    for key in ("domain", "company", "nis2_in_scope", "nis2_verdict", "nis2_sector",
                "email_weakness", "ciso_status", "finding_count", "max_severity",
                "talking_point", "findings", "signals_ran"):
        assert key in out, f"missing {key}"
    assert out["nis2_in_scope"] is True
    assert out["nis2_sector"] == "Energy"
    assert isinstance(out["findings"], list)
    # run_network=False must not claim the network signals ran
    assert "attack_surface" not in out["signals_ran"]


def test_enrich_out_of_scope_company():
    out = enrich_domain(
        {"domain": "smallshop.se", "name": "Small Shop AB",
         "sni_code": "10200", "employees": 20, "turnover_eur": 3_000_000},
        backend=_backend(), run_network=False,
    )
    assert out["nis2_in_scope"] is False
