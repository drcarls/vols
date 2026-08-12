from presales_scout.collectors import nis2
from presales_scout.models import Company


def test_transport_large_in_scope():
    v = nis2.qualify(Company(name="Nordfrakt", sni_code="49410", employees=180))
    assert v.verdict == "in_scope"
    assert v.sector == "Transport"


def test_transport_unknown_size_likely():
    v = nis2.qualify(Company(name="Nordfrakt", sni_code="49410"))
    assert v.verdict == "likely_in_scope"


def test_small_food_out_of_scope():
    v = nis2.qualify(Company(name="Foods", sni_code="10200", employees=30, turnover_eur=6_000_000))
    assert v.verdict == "out_of_scope"


def test_turnover_over_threshold_in_scope():
    v = nis2.qualify(Company(name="Energy", sni_code="35120", employees=20, turnover_eur=90_000_000))
    assert v.verdict == "in_scope"


def test_digital_infra_regardless_of_size():
    v = nis2.qualify(Company(name="DataHall", sni_code="63110", employees=12))
    assert v.verdict == "in_scope"
    assert v.meets_size_threshold is True


def test_non_sector_out_of_scope():
    v = nis2.qualify(Company(name="Consulting", sni_code="70220", employees=500))
    assert v.verdict == "out_of_scope"
    assert v.sector is None


def test_missing_sni_unknown():
    v = nis2.qualify(Company(name="Mystery"))
    assert v.verdict == "unknown"
