from gallica_le_temps.alto import parse_alto
from gallica_le_temps.locate import (
    bounding_region,
    find_anchor,
    locate_value,
    normalize,
    value_after_anchor,
)


def test_normalize_strips_accents_and_case():
    assert normalize("Fédéré") == "federe"
    assert normalize("  Banque ") == "banque"


def test_find_anchor_multiword(alto_xml):
    words = parse_alto(alto_xml)
    matches = find_anchor(words, "Banque de France")
    assert len(matches) == 1
    assert [w.content for w in matches[0]] == ["Banque", "de", "France"]


def test_find_anchor_accent_insensitive(alto_xml):
    words = parse_alto(alto_xml)
    # Query with different case/accents still matches the OCR'd tokens.
    assert find_anchor(words, "banque DE france")


def test_value_after_anchor(alto_xml):
    words = parse_alto(alto_xml)
    anchor = find_anchor(words, "Banque de France")[0]
    value = value_after_anchor(words, anchor)
    assert [w.content for w in value] == ["84,25"]


def test_value_after_rente_anchor(alto_xml):
    words = parse_alto(alto_xml)
    anchor = find_anchor(words, "3 0/0")[0]
    value = value_after_anchor(words, anchor)
    # "0/0" is part of the anchor; the value is the quotation that follows.
    assert [w.content for w in value] == ["83,50"]


def test_locate_value_region(alto_xml):
    words = parse_alto(alto_xml)
    region = locate_value(words, ["Banque de France"], pad_ratio=0.0)
    assert region.hpos == 600 and region.vpos == 200
    assert region.width == 120 and region.height == 40


def test_locate_value_includes_anchor(alto_xml):
    words = parse_alto(alto_xml)
    region = locate_value(
        words, ["Banque de France"], include_anchor=True, pad_ratio=0.0
    )
    # Region now spans from "Banque" (HPOS 100) to end of "84,25" (720).
    assert region.hpos == 100
    assert region.hpos + region.width == 720


def test_locate_value_tries_anchor_variants(alto_xml):
    words = parse_alto(alto_xml)
    # First variant never appears; second one does.
    region = locate_value(words, ["Nonexistent Label", "3 0/0"], pad_ratio=0.0)
    assert region is not None
    assert region.text == "83,50"


def test_locate_value_none_when_no_anchor(alto_xml):
    words = parse_alto(alto_xml)
    assert locate_value(words, ["Wall Street"]) is None


def test_pad_region_clamps_to_page(alto_xml):
    words = parse_alto(alto_xml)
    region = locate_value(words, ["Banque de France"], pad_ratio=1.0)
    # padding = 40px -> left/top grow but stay >= 0, right/bottom within page.
    assert region.hpos == 560 and region.vpos == 160
    assert region.hpos + region.width <= region.page_width


def test_bounding_region_requires_words():
    import pytest

    with pytest.raises(ValueError):
        bounding_region([])
