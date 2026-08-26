"""Normalisation must be strict: anything ambiguous is rejected with a reason."""

import pytest

from app.services.normalize import (NormalizationError, dedupe,
                                    normalize_domain, split_public_suffix)


@pytest.mark.parametrize("raw,expected", [
    ("example.com", "example.com"),
    ("  EXAMPLE.COM  ", "example.com"),
    ("https://www.Example.com/path?q=1", "example.com"),
    ("www.example.com.", "example.com"),
    ("example.com:8080", "example.com"),
    ("sub.example.com", "example.com"),
    ("shop.example.co.uk", "example.co.uk"),
    ("EXAMPLE.CO.UK", "example.co.uk"),
])
def test_normalises_to_registrable_name(raw, expected):
    assert normalize_domain(raw).name == expected


def test_splits_multi_label_public_suffix():
    assert split_public_suffix(["shop", "example", "co", "uk"]) == ("example", "co.uk")
    assert split_public_suffix(["example", "com"]) == ("example", "com")


def test_internationalised_name_becomes_punycode_and_keeps_unicode():
    result = normalize_domain("münchen.de")
    assert result.name == "xn--mnchen-3ya.de"
    assert result.is_idn is True
    assert result.unicode_name == "münchen.de"


@pytest.mark.parametrize("raw", ["", "   ", "nodots", "bad_domain.com",
                                 "-leading.com", "trailing-.com", None])
def test_rejects_rather_than_coercing(raw):
    with pytest.raises(NormalizationError):
        normalize_domain(raw)


def test_rejection_carries_a_reason():
    with pytest.raises(NormalizationError) as exc:
        normalize_domain("nodots")
    assert "TLD" in str(exc.value)


def test_dedupe_preserves_order_and_counts():
    order, dupes = dedupe(["a.com", "b.com", "a.com", "a.com"])
    assert order == ["a.com", "b.com"]
    assert dupes == {"a.com": 3}
