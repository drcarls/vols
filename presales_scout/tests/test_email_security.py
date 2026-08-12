from presales_scout.collectors.email_security import evaluate_records


def test_no_dmarc_is_weak():
    sig = evaluate_records(["v=spf1 include:_spf.google.com ~all"], [])
    assert sig.weakness == "weak"
    assert sig.has_spf is True
    assert sig.has_dmarc is False


def test_dmarc_policy_none_is_weak():
    sig = evaluate_records(
        ["v=spf1 -all"], ["v=DMARC1; p=none; rua=mailto:a@x.se"]
    )
    assert sig.weakness == "weak"
    assert sig.dmarc_policy == "none"


def test_enforced_dmarc_with_spf_is_strong():
    sig = evaluate_records(
        ["v=spf1 -all"], ["v=DMARC1; p=reject; rua=mailto:a@x.se"]
    )
    assert sig.weakness == "strong"
    assert sig.dmarc_policy == "reject"


def test_dmarc_enforced_without_spf_is_partial():
    sig = evaluate_records([], ["v=DMARC1; p=quarantine"])
    assert sig.weakness == "partial"
