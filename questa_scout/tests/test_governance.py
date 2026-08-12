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


class _NoiseBackend:
    """Returns real governance-leader profiles that belong to OTHER companies
    -- the exact noise a live SERP returns for a company-specific query."""

    def search(self, query, *, country="us", language="en"):
        from questa_scout.collectors.serp import SerpResult
        return [
            SerpResult("https://www.linkedin.com/in/a", "Cari Benn - Chief Privacy Officer @ Microsoft", "CPO at Microsoft"),
            SerpResult("https://www.linkedin.com/in/b", "Kimberly Gray - Chief Privacy Officer; IQVIA", "CPO at IQVIA"),
        ]


def test_unrelated_leader_profiles_are_ignored():
    # None of the returned CPOs work at the target company, so the signal is
    # none_found (a real opening to verify) -- never a false 'uncertain'.
    sig = ai_governance.detect_governance(Company(name="Meridian Trust Bank"), _NoiseBackend())
    assert sig.status == "none_found"
    assert sig.people == []
