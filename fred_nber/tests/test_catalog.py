"""Catalog defaults and YAML override."""

from fred_nber.catalog import catalog_by_series, default_catalog, load_catalog


def test_default_catalog():
    cat = default_catalog()
    assert cat.benchmark.series == "benchmark"
    assert cat.benchmark.fred_id == "M1341CGB40000M156NNBR"
    by = catalog_by_series(cat)
    assert set(by) == {"france", "germany"}
    assert by["france"].fred_id == "M13027FRM156NNBR"
    assert by["germany"].fred_id == "M1328ADEM193NNBR"


def test_load_yaml(tmp_path):
    p = tmp_path / "s.yaml"
    p.write_text(
        "benchmark:\n"
        "  series: benchmark\n"
        "  fred_id: BENCH1\n"
        "  label: Consols\n"
        "issuers:\n"
        "  - series: france\n"
        "    fred_id: FR1\n"
        "    label: France\n",
        encoding="utf-8",
    )
    cat = load_catalog(str(p))
    assert cat.benchmark.fred_id == "BENCH1"
    assert cat.issuers[0].series == "france" and cat.issuers[0].fred_id == "FR1"
