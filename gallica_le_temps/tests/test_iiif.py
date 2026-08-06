from gallica_le_temps.alto import parse_alto
from gallica_le_temps.iiif import (
    PixelRegion,
    crop_url,
    full_size_from_info,
    info_url,
    region_crop_url,
    scale_region,
)
from gallica_le_temps.locate import locate_value


def test_info_url():
    assert info_url("bpt6k239abcd", 3).endswith("/bpt6k239abcd/f3/info.json")


def test_full_size_from_info(iiif_info):
    assert full_size_from_info(iiif_info) == (5000, 8000)


def test_scale_region_doubles(alto_xml, iiif_info):
    # ALTO page is 2500x4000, IIIF full image 5000x8000 -> 2x scale.
    words = parse_alto(alto_xml)
    region = locate_value(words, ["Banque de France"], pad_ratio=0.0)
    w, h = full_size_from_info(iiif_info)
    pixel = scale_region(region, w, h)
    assert pixel.x == 1200 and pixel.y == 400
    assert pixel.w == 240 and pixel.h == 80


def test_scale_region_clamps_within_image(alto_xml):
    words = parse_alto(alto_xml)
    region = locate_value(words, ["Banque de France"], pad_ratio=0.0)
    # Absurdly small IIIF image forces clamping to keep the crop in-bounds.
    pixel = scale_region(region, 100, 100)
    assert 0 <= pixel.x <= 100
    assert pixel.x + pixel.w <= 100
    assert pixel.y + pixel.h <= 100
    assert pixel.w >= 1 and pixel.h >= 1


def test_crop_url_format():
    region = PixelRegion(1200, 400, 240, 80)
    url = crop_url("bpt6k239abcd", 3, region)
    assert url == (
        "https://gallica.bnf.fr/iiif/ark:/12148/bpt6k239abcd/f3/"
        "1200,400,240,80/full/0/native.jpg"
    )


def test_region_crop_url_scales(alto_xml, iiif_info):
    words = parse_alto(alto_xml)
    region = locate_value(words, ["Banque de France"], pad_ratio=0.0)
    w, h = full_size_from_info(iiif_info)
    url = region_crop_url("bpt6k239abcd", 3, region, w, h)
    assert "1200,400,240,80" in url
