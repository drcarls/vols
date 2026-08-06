from gallica_le_temps.config import RunConfig, TargetSpec
from gallica_le_temps.pipeline import Pipeline, collect, write_csv


def _config(**overrides):
    base = dict(
        date_start="1914-07-28",
        date_end="1914-07-28",
        targets=[
            TargetSpec(name="bdf", anchors=["Banque de France"], page=1, pad_ratio=0.0),
            TargetSpec(name="rente", anchors=["3 0/0"], page=1, pad_ratio=0.0),
        ],
        min_ocr_quality=80.0,
    )
    base.update(overrides)
    return RunConfig(**base)


class FixedExtractor:
    def __init__(self, text):
        self.text = text

    def extract(self, image_bytes):
        return self.text


def test_pipeline_locates_and_builds_crop_urls(
    fake_client_factory, sru_xml, alto_xml, iiif_info
):
    client = fake_client_factory(
        text_routes={"SRU": sru_xml, "RequestDigitalElement": alto_xml},
        json_routes={"info.json": iiif_info},
    )
    rows = collect(Pipeline(client).run(_config()))

    assert {r.target for r in rows} == {"bdf", "rente"}
    bdf = next(r for r in rows if r.target == "bdf")
    assert bdf.status == "ok"
    assert bdf.ark == "bpt6k239abcd"
    assert bdf.ocr_quality == 95.36
    assert bdf.anchor_text == "84,25"
    # ALTO 600,200,120,40 scaled 2x -> IIIF 1200,400,240,80.
    assert bdf.region == "1200,400,240,80"
    assert "1200,400,240,80" in bdf.crop_url


def test_pipeline_with_ocr_extractor_parses_value(
    fake_client_factory, sru_xml, alto_xml, iiif_info
):
    client = fake_client_factory(
        text_routes={"SRU": sru_xml, "RequestDigitalElement": alto_xml},
        json_routes={"info.json": iiif_info},
        bytes_routes={"iiif": b"fake-jpeg-bytes"},
    )
    pipeline = Pipeline(client, extractor=FixedExtractor("84,25"))
    rows = collect(pipeline.run(_config(targets=[
        TargetSpec(name="bdf", anchors=["Banque de France"], page=1, pad_ratio=0.0),
    ])))
    assert rows[0].ocr_text == "84,25"
    assert rows[0].value == "84.25"
    assert rows[0].status == "ok"


def test_pipeline_no_issue_when_sru_empty(fake_client_factory):
    empty = (
        '<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">'
        "<srw:numberOfRecords>0</srw:numberOfRecords></srw:searchRetrieveResponse>"
    )
    client = fake_client_factory(text_routes={"SRU": empty})
    rows = collect(Pipeline(client).run(_config()))
    assert all(r.status == "no_issue" for r in rows)


def test_pipeline_low_quality_when_below_floor(fake_client_factory, alto_xml, iiif_info):
    # SRU record reports ocr quality 60, below the config floor of 80.
    low_sru = (
        '<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">'
        "<srw:numberOfRecords>1</srw:numberOfRecords><srw:records><srw:record>"
        "<srw:recordData><oai_dc:dc "
        'xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/">'
        "<dc:date>1914-07-28</dc:date>"
        "<dc:identifier>https://gallica.bnf.fr/ark:/12148/bpt6klowq</dc:identifier>"
        "</oai_dc:dc></srw:recordData>"
        "<srw:extraRecordData><ocrQuality>60.0</ocrQuality></srw:extraRecordData>"
        "</srw:record></srw:records></srw:searchRetrieveResponse>"
    )
    client = fake_client_factory(text_routes={"SRU": low_sru})
    rows = collect(Pipeline(client).run(_config()))
    assert all(r.status == "low_quality" for r in rows)
    assert all(r.ocr_quality == 60.0 for r in rows)
    # ALTO must NOT be fetched for a rejected issue.
    assert not any("RequestDigitalElement" in c for c in client.calls)


def test_pipeline_not_found_when_anchor_absent(
    fake_client_factory, sru_xml, alto_xml, iiif_info
):
    client = fake_client_factory(
        text_routes={"SRU": sru_xml, "RequestDigitalElement": alto_xml},
        json_routes={"info.json": iiif_info},
    )
    cfg = _config(targets=[
        TargetSpec(name="wallst", anchors=["Wall Street"], page=1),
    ])
    rows = collect(Pipeline(client).run(cfg))
    assert rows[0].status == "not_found"


def test_alto_is_cached_across_targets(
    fake_client_factory, sru_xml, alto_xml, iiif_info
):
    client = fake_client_factory(
        text_routes={"SRU": sru_xml, "RequestDigitalElement": alto_xml},
        json_routes={"info.json": iiif_info},
    )
    collect(Pipeline(client).run(_config()))
    # Two targets on the same page -> ALTO fetched once, not twice.
    alto_calls = [c for c in client.calls if "RequestDigitalElement" in c]
    assert len(alto_calls) == 1


def test_write_csv(tmp_path, fake_client_factory, sru_xml, alto_xml, iiif_info):
    client = fake_client_factory(
        text_routes={"SRU": sru_xml, "RequestDigitalElement": alto_xml},
        json_routes={"info.json": iiif_info},
    )
    rows = collect(Pipeline(client).run(_config()))
    out = tmp_path / "out.csv"
    write_csv(rows, str(out))
    text = out.read_text(encoding="utf-8")
    assert "date,target,status" in text.splitlines()[0]
    assert "bdf" in text and "1200,400,240,80" in text
