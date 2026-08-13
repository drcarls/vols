"""Tests for the external-hygiene benchmark scoring."""

from presales_scout import benchmark


def test_perfect_score_when_no_findings():
    assert benchmark.hygiene_score([]) == 100


def test_score_is_100_minus_weighted_penalty():
    # severity_score 3 -> 10, 4 -> 16  => 100 - 26 = 74
    findings = [("WEB_CSP_MISSING", 3), ("WEB_COMPONENT_EOL", 4)]
    assert benchmark.hygiene_score(findings) == 74


def test_governance_and_supply_excluded():
    # only the EMAIL finding (sev 3 -> 10) counts; GOV/SUPPLY are other axes
    findings = [("EMAIL_DMARC_UNENFORCED", 3), ("GOV_NO_CISO", 3), ("SUPPLY_UNMANAGED", 3)]
    assert benchmark.hygiene_score(findings) == 90


def test_score_clamps_at_zero():
    findings = [("X", 5)] * 10  # 240 penalty
    assert benchmark.hygiene_score(findings) == 0


def test_accepts_finding_objects():
    from presales_scout.models import Finding

    f = Finding(company="C", domain="c.se", finding_id="WEB_HSTS_MISSING", title="t",
                category="transport_encryption", severity="medium", severity_score=3,
                evidence="e", risk="r", nis2_measure="Art. 21(2)(h)", iso_control="A.8.24",
                service="s", remediation="rem", talking_point="tp")
    assert benchmark.hygiene_score([f]) == 90


def test_rank_orders_and_bands():
    data = {
        "Clean Co": [("WEB_CSP_MISSING", 1)],                       # 97
        "Middling Co": [("A", 3), ("B", 3)],                        # 80
        "Weak Co": [("A", 4), ("B", 4), ("C", 3), ("D", 3)],        # 100-52 = 48
        "Exposed Co": [("A", 5), ("B", 4), ("C", 4), ("D", 3)],     # 100-66 = 34
    }
    rows = benchmark.rank(data)
    assert [r["name"] for r in rows] == ["Clean Co", "Middling Co", "Weak Co", "Exposed Co"]
    assert rows[0]["rank"] == 1 and rows[0]["percentile"] == 100
    assert rows[-1]["percentile"] == 0
    assert rows[0]["band"] == "strong" and rows[-1]["band"] == "exposed"
