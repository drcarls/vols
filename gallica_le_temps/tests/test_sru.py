from gallica_le_temps.sru import (
    build_issue_query,
    build_sru_params,
    format_ocr_threshold,
    parse_sru_response,
    sru_number_of_records,
)


def test_format_ocr_threshold_zero_pads():
    assert format_ocr_threshold(80) == "080.00"
    assert format_ocr_threshold(5.5) == "005.50"
    assert format_ocr_threshold(100) == "100.00"


def test_build_issue_query_uses_publication_date_and_adds_quality():
    q = build_issue_query("1914-07-28", min_ocr_quality=80)
    assert 'arkPress all "cb34431794k_date"' in q
    assert 'gallicapublication_date="1914/07/28"' in q
    assert 'ocrquality > "080.00"' in q


def test_build_issue_query_without_quality():
    q = build_issue_query("1931-09-21")
    assert q == (
        'arkPress all "cb34431794k_date" '
        'and gallicapublication_date="1931/09/21"'
    )


def test_build_issue_query_rejects_bad_date():
    import pytest

    with pytest.raises(ValueError):
        build_issue_query("28-07-1914")


def test_build_sru_params():
    p = build_sru_params("q", maximum_records=3)
    assert p["operation"] == "searchRetrieve"
    assert p["version"] == "1.2"
    assert p["maximumRecords"] == "3"


def test_parse_sru_response(sru_xml):
    records = parse_sru_response(sru_xml)
    assert len(records) == 1
    rec = records[0]
    assert rec.ark == "bpt6k239abcd"
    assert rec.date == "1914-07-28"
    assert rec.title == "Le Temps"
    assert rec.ocr_quality == 95.36


def test_number_of_records(sru_xml):
    assert sru_number_of_records(sru_xml) == 1


def test_parse_prefers_document_ark_over_title_ark():
    # Current Gallica: dc:identifier carries the parent *title* ARK (cb…), while
    # the issue's own document ARK (bpt6k…) lives in Gallica-namespace fields.
    xml = (
        '<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/"'
        ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
        ' xmlns:gallica="http://gallica.bnf.fr/namespaces/gallica/">'
        "<srw:numberOfRecords>1</srw:numberOfRecords><srw:records><srw:record>"
        "<srw:recordData><oai_dc><dc:identifier>"
        "https://gallica.bnf.fr/ark:/12148/cb34431794k/date</dc:identifier>"
        "<dc:date>1914-07-31</dc:date><dc:title>Le Temps</dc:title>"
        "<gallica:uri>bpt6k2418864</gallica:uri>"
        "<gallica:highres>https://gallica.bnf.fr/ark:/12148/bpt6k2418864.highres"
        "</gallica:highres></oai_dc></srw:recordData>"
        "</srw:record></srw:records></srw:searchRetrieveResponse>"
    )
    recs = parse_sru_response(xml)
    assert len(recs) == 1
    assert recs[0].ark == "bpt6k2418864"   # not cb34431794k


def test_parse_empty_response():
    empty = (
        '<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">'
        "<srw:numberOfRecords>0</srw:numberOfRecords>"
        "<srw:records></srw:records></srw:searchRetrieveResponse>"
    )
    assert parse_sru_response(empty) == []
    assert sru_number_of_records(empty) == 0
