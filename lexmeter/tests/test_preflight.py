import yaml
from conftest import CONFIG

from lexmeter_fees.preflight import load_preflight


def test_current_policy_is_not_yet_certifiable():
    # All three prerequisites are still open. The suite asserts it so the gap
    # cannot quietly close by being forgotten rather than resolved.
    pre = load_preflight(CONFIG / "collection_policy.yaml")
    assert pre.certifiable is False
    assert len(pre.blockers) == 3


def test_each_blocker_names_its_method_statement_section():
    pre = load_preflight(CONFIG / "collection_policy.yaml")
    for blocker in pre.blockers:
        assert "section 7" in blocker


def test_named_provider_without_attestation_still_blocks(tmp_path):
    # A vendor on paper is not provenance. The attestation is the artefact that
    # survives cross-examination.
    doc = yaml.safe_load((CONFIG / "collection_policy.yaml").read_text())
    doc["egress"]["provider"] = "SomeVendor"
    doc["egress"]["attestation_on_file"] = False
    path = tmp_path / "policy.yaml"
    path.write_text(yaml.safe_dump(doc))
    blockers = load_preflight(path).blockers
    assert any("attestation_on_file is false" in b for b in blockers)


def test_fully_configured_policy_passes(tmp_path):
    doc = yaml.safe_load((CONFIG / "collection_policy.yaml").read_text())
    doc["egress"]["provider"] = "SomeVendor"
    doc["egress"]["attestation_on_file"] = True
    doc["evidence"]["timestamp_authority"] = "https://tsa.example/rfc3161"
    doc["evidence"]["custodian"] = "Named Person"
    path = tmp_path / "policy.yaml"
    path.write_text(yaml.safe_dump(doc))
    assert load_preflight(path).certifiable is True
