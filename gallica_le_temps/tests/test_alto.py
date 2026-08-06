from gallica_le_temps.alto import alto_url, parse_alto


def test_alto_url():
    assert (
        alto_url("bpt6k239abcd", 3)
        == "https://gallica.bnf.fr/RequestDigitalElement?O=bpt6k239abcd&E=ALTO&Deb=3"
    )


def test_parse_alto_reads_all_tokens(alto_xml):
    words = parse_alto(alto_xml)
    contents = [w.content for w in words]
    assert contents == ["COURS", "Banque", "de", "France", "84,25", "3", "0/0", "83,50"]


def test_parse_alto_orders_lines_top_to_bottom(alto_xml):
    # "COURS" (VPOS=120) is authored last but has the smallest VPOS, so it must
    # come first after vertical sorting.
    words = parse_alto(alto_xml)
    assert words[0].content == "COURS"
    assert words[0].line_id == 0


def test_parse_alto_carries_page_dimensions(alto_xml):
    words = parse_alto(alto_xml)
    assert all(w.page_width == 2500 and w.page_height == 4000 for w in words)


def test_wordbox_geometry(alto_xml):
    words = parse_alto(alto_xml)
    banque = next(w for w in words if w.content == "Banque")
    assert banque.right == 280  # 100 + 180
    assert banque.bottom == 240  # 200 + 40
    assert banque.cx == 190


def test_same_line_order(alto_xml):
    words = parse_alto(alto_xml)
    line1 = [w for w in words if w.content in ("Banque", "de", "France", "84,25")]
    assert all(w.line_id == line1[0].line_id for w in line1)
    assert [w.order for w in line1] == [0, 1, 2, 3]


def test_parse_alto_empty_page():
    assert parse_alto("<alto></alto>") == []
