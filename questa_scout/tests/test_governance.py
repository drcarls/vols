from conftest import fixtures_serp

from questa_scout.collectors import ai_governance
from questa_scout.collectors.serp import FixtureBackend
from questa_scout.models import Company


def _backend():
    return FixtureBackend(fixtures_serp())


def test_visible_cpo_is_governed():
    sig = ai_governance.detect_governance(
        Company(name="Meridian Trust Bank"), _backend()
    )
    assert sig.status == "governed"
    assert sig.verify_recommended is False
    assert any(p.role_tier == "leader" for p in sig.people)


def test_only_analyst_is_uncertain():
    sig = ai_governance.detect_governance(
        Company(name="BrightClaim BPO Inc"), _backend()
    )
    assert sig.status == "uncertain"
    assert sig.verify_recommended is True


def test_no_hit_is_none_found():
    sig = ai_governance.detect_governance(
        Company(name="Cascade Health Partners"), _backend()
    )
    assert sig.status == "none_found"
    assert sig.verify_recommended is True
