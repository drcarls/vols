from datetime import date

import pytest

from lexmeter_fees.evidence import (
    DailyAnchor,
    NullTimestampAuthority,
    build_daily_anchor,
    canonical_json,
    content_path,
    merkle_root,
    record_digest,
)


def test_canonical_json_is_key_order_independent():
    assert canonical_json({"b": 1, "a": 2}) == canonical_json({"a": 2, "b": 1})


def test_record_digest_is_stable_across_equal_records():
    a = {"company": "X", "fees": [{"label": "Service", "cents": 100}]}
    b = {"fees": [{"cents": 100, "label": "Service"}], "company": "X"}
    assert record_digest(a) == record_digest(b)


def test_record_digest_changes_on_any_substantive_edit():
    base = {"cents": 100}
    assert record_digest(base) != record_digest({"cents": 101})


def test_merkle_root_depends_on_the_set_not_the_read_order():
    leaves = ["aa" * 32, "bb" * 32, "cc" * 32]
    assert merkle_root(leaves) == merkle_root(list(reversed(leaves)))


def test_merkle_root_detects_a_single_altered_leaf():
    leaves = ["aa" * 32, "bb" * 32, "cc" * 32]
    tampered = ["aa" * 32, "bb" * 31 + "bc", "cc" * 32]
    assert merkle_root(leaves) != merkle_root(tampered)


def test_merkle_root_detects_a_removed_leaf():
    leaves = ["aa" * 32, "bb" * 32, "cc" * 32]
    assert merkle_root(leaves) != merkle_root(leaves[:2])


def test_odd_leaf_count_is_handled():
    for n in (1, 2, 3, 5, 9):
        assert len(merkle_root([f"{i:064x}" for i in range(n)])) == 64


def test_empty_leaf_set_refuses_to_anchor():
    with pytest.raises(ValueError):
        merkle_root([])


def test_content_path_fans_out_by_digest_prefix():
    assert content_path("abcd" + "0" * 60, ".png").startswith("ab/cd/abcd")


def test_null_tsa_refuses_rather_than_pretending():
    # An unanchored chain that looks anchored fails at the point of use, which is
    # the worst possible moment, so the default must raise.
    with pytest.raises(NotImplementedError):
        NullTimestampAuthority().stamp("00" * 32)


def test_anchor_without_a_tsa_is_marked_unanchored():
    anchor = build_daily_anchor(date(2026, 9, 14), ["aa" * 32], NullTimestampAuthority())
    assert isinstance(anchor, DailyAnchor)
    assert anchor.externally_anchored is False
    assert anchor.leaf_count == 1
