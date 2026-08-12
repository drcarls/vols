from presales_scout.collectors.ciso import query


def test_build_query_shape():
    q = query.build_query("Acme AB")
    assert "site:linkedin.com/in" in q
    assert '"Acme AB"' in q
    assert "CISO" in q
    assert "sakerhetschef" in q  # Swedish recall term included


def test_classify_title_leader_vs_generic():
    assert query.classify_title("CISO at Acme") == "leader"
    assert query.classify_title("Head of Information Security") == "leader"
    assert query.classify_title("informationssakerhetschef") == "leader"
    # Bare Swedish sakerhetschef can be physical security -> weaker tier
    assert query.classify_title("Sakerhetschef pa Acme") == "generic"
    assert query.classify_title("Security Analyst") == "generic"
    assert query.classify_title("Head of Marketing") is None


def test_classify_title_handles_diacritics():
    assert query.classify_title("Informationssäkerhetschef") == "leader"


def test_is_linkedin_profile():
    assert query.is_linkedin_profile("https://www.linkedin.com/in/anna")
    assert not query.is_linkedin_profile("https://linkedin.com/company/acme")
    assert not query.is_linkedin_profile("https://acme.se")


def test_company_mentioned_ignores_suffix():
    assert query.company_mentioned("Nordfrakt Logistik AB", "CISO at Nordfrakt Logistik")
    assert not query.company_mentioned("Nordfrakt Logistik AB", "CISO at Volvo")


def test_parse_person():
    name, role = query.parse_person("Anna Svensson - CISO - Nordfrakt Logistik AB | LinkedIn")
    assert name == "Anna Svensson"
    assert "CISO" in role
