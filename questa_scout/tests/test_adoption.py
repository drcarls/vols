from conftest import fixtures_serp

from questa_scout.collectors import ai_adoption
from questa_scout.collectors.serp import FixtureBackend
from questa_scout.models import Company


def _backend():
    return FixtureBackend(fixtures_serp())


def test_strong_genai_hiring_is_active():
    sig = ai_adoption.detect_adoption(
        Company(name="Cascade Health Partners", naics_code="621111"),
        _backend(),
        check_web=False,
    )
    assert sig.level == "active"
    assert sig.hiring is True


def test_only_data_scientist_is_emerging():
    sig = ai_adoption.detect_adoption(
        Company(name="Meridian Trust Bank", naics_code="522110"),
        _backend(),
        check_web=False,
    )
    assert sig.level == "emerging"


def test_no_jobs_and_no_web_is_unknown():
    sig = ai_adoption.detect_adoption(
        Company(name="No Signal Inc"),
        _backend(),
        check_web=False,
    )
    assert sig.level == "unknown"
