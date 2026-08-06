"""Catalogue loading and the verified request-serialisation contract."""

from imm_yale.client import Query
from imm_yale.config import (
    catalogue_series,
    default_catalogue,
    load_catalogue,
)


def test_default_catalogue_covers_the_four_powers():
    cat = default_catalogue()
    series = set(catalogue_series(cat))
    assert series == {"france", "germany", "russia", "austria_hungary"}
    assert cat.benchmark.series == "benchmark"


def test_load_catalogue_yaml(tmp_path):
    p = tmp_path / "sec.yaml"
    p.write_text(
        "benchmark:\n"
        "  series: benchmark\n"
        "  label: Consols\n"
        "  security_id: '10500'\n"
        "issuers:\n"
        "  - series: germany\n"
        "    label: German 3%\n"
        "    security_id: '10777'\n",
        encoding="utf-8",
    )
    cat = load_catalogue(str(p))
    assert cat.benchmark.security_id == "10500"
    assert cat.issuers[0].series == "germany"
    assert cat.issuers[0].security_id == "10777"


def test_query_byid_serialisation():
    q = Query(start_year=1904, end_year=1914, security_ids=["10500"])
    f = q.form_fields()
    assert ("stype", "byid") in f
    assert ("securityID[]", "10500") in f
    assert ("StYear", "1904") in f and ("EndYear", "1914") in f
    # yield group is requested under Var7[]
    assert ("Var7[]", "YieldInvtLatePricePound") in f
    assert ("format", "html") in f


def test_query_partial_name_uses_cname_field():
    # The backend reads the partial-name value from `cname`, not `pcname`.
    q = Query(start_year=1904, end_year=1914, name_partial="Russian")
    f = q.form_fields()
    assert ("stype", "comname") in f
    assert ("cname", "Russian") in f


def test_query_exact_name_uses_ecname_field():
    q = Query(start_year=1904, end_year=1914, name_exact="Consols")
    f = q.form_fields()
    assert ("stype", "cname") in f
    assert ("ecname", "Consols") in f


def test_query_requires_a_selector():
    import pytest

    with pytest.raises(ValueError):
        Query(start_year=1904, end_year=1914).form_fields()
