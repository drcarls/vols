from questa_scout.collectors.enrich import pick_domain, _norm


def test_exact_name_match():
    sugg = [
        {"name": "Stripe", "domain": "stripe.com"},
        {"name": "Stripes", "domain": "stripes.co"},
    ]
    assert pick_domain(sugg, "Stripe, Inc.") == "stripe.com"


def test_legal_suffix_stripped_for_match():
    sugg = [{"name": "Cascade Health", "domain": "cascadehealth.com"}]
    assert pick_domain(sugg, "Cascade Health Partners LLC") == "cascadehealth.com"


def test_no_reasonable_match_returns_none():
    sugg = [{"name": "Completely Different Co", "domain": "different.com"}]
    assert pick_domain(sugg, "Meridian Trust Bank") is None


def test_empty_suggestions_returns_none():
    assert pick_domain([], "Anything Inc") is None


def test_norm_folds_ampersand_and_punct():
    assert _norm("Harbor & Vale, LLP") == "harbor and vale"
