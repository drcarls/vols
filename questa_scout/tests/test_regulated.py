from questa_scout.collectors import regulated
from questa_scout.models import Company


def test_healthcare_is_phi_hipaa():
    v = regulated.qualify(Company(name="Cascade Health Partners", naics_code="621111", employees=900))
    assert v.verdict == "in_scope"
    assert v.data_class == "PHI"
    assert v.regime == "HIPAA"
    assert v.sensitivity == 4


def test_bank_is_financial_glba():
    v = regulated.qualify(Company(name="Meridian Trust Bank", naics_code="522110", employees=1200))
    assert v.verdict == "in_scope"
    assert v.data_class == "financial"
    assert "GLBA" in v.regime


def test_longest_prefix_wins():
    # 5411 (legal) is more specific than 54 -- should map to legal_privileged.
    v = regulated.qualify(Company(name="Harbor & Vale LLP", naics_code="541110", employees=220))
    assert v.data_class == "legal_privileged"
    assert v.sector == "Legal services"


def test_non_regulated_out_of_scope():
    v = regulated.qualify(Company(name="TinyShop LLC", naics_code="448140", employees=15))
    assert v.verdict == "out_of_scope"
    assert v.data_class is None


def test_missing_naics_is_unknown():
    v = regulated.qualify(Company(name="Mystery Co", naics_code=None))
    assert v.verdict == "unknown"


def test_small_regulated_is_likely_scope():
    v = regulated.qualify(Company(name="Tiny Clinic", naics_code="621111", employees=8))
    assert v.verdict == "likely_in_scope"
    assert v.data_class == "PHI"
