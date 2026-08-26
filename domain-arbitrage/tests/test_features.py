"""Feature extraction is deterministic. These tests pin behaviour, not taste."""

import pytest

from app.scoring.features import extract_features
from app.scoring.lexicon import count_syllables, looks_plural, segment


@pytest.mark.parametrize("text,expected", [
    ("datacentercooling", ("data", "center", "cooling")),
    ("berlinroofing", ("berlin", "roofing")),
    ("fleetanalytics", ("fleet", "analytics")),
    ("cloudsecurity", ("cloud", "security")),
    ("getflow", ("get", "flow")),
])
def test_segmentation_finds_the_intended_words(text, expected):
    assert segment(text)[0] == expected


def test_segmentation_does_not_shred_unknown_strings():
    tokens, confidence = segment("xkqzp")
    assert tokens == ("xkqzp",)
    assert confidence == 0.0


def test_segmentation_is_deterministic():
    assert segment("fleetanalytics") == segment("fleetanalytics")


@pytest.mark.parametrize("word,count", [("cooling", 2), ("data", 2),
                                        ("analytics", 4), ("flow", 1)])
def test_syllable_counting(word, count):
    assert count_syllables(word) == count


@pytest.mark.parametrize("word,plural", [("loans", True), ("quotes", True),
                                         ("glass", False), ("news", False),
                                         ("business", False)])
def test_plural_detection_handles_the_classic_traps(word, plural):
    assert looks_plural(word) is plural


def test_structural_features_of_a_clean_two_word_com():
    f = extract_features("fleetanalytics", "com")
    assert f.word_count == 2
    assert f.words == ["fleet", "analytics"]
    assert f.all_words_dictionary is True
    assert f.has_hyphen is False and f.has_digit is False
    assert f.sld_length == 14
    assert f.length == 18


def test_defects_are_detected():
    f = extract_features("get-cheap-loans-4u", "net")
    assert f.has_hyphen is True
    assert f.hyphen_count == 3
    assert f.has_digit is True
    assert f.has_generic_modifier is True


def test_unpronounceable_strings_are_not_brandable():
    junk = extract_features("xkqzp", "io")
    real = extract_features("zillow", "com")
    assert junk.pronounceability < 50
    assert junk.brandability < real.brandability


def test_all_linguistic_scores_are_bounded():
    for sld in ["fleetanalytics", "xkqzp", "get-cheap-loans-4u", "a1", "flow"]:
        f = extract_features(sld, "com")
        for name in ("pronounceability", "memorability", "spelling_ambiguity",
                     "semantic_coherence", "brandability",
                     "business_name_plausibility"):
            value = getattr(f, name)
            assert 0.0 <= value <= 100.0, f"{name}={value} for {sld}"


def test_acronym_detection():
    assert extract_features("qzr", "com").acronym_likelihood > 0.7
    assert extract_features("berlinroofing", "com").acronym_likelihood < 0.2
