"""The £-s-d yield conversion — pure arithmetic, pinned to worked examples."""

import math

import pytest

from imm_yale.lsd import cells_to_percent, lsd_to_percent, parse_number


def test_worked_example_four_three_six():
    # £4 3s 6d % = 4 + 3/20 + 6/240 = 4.175
    assert lsd_to_percent(4, 3, 6) == pytest.approx(4.175)


def test_whole_pounds_only():
    assert lsd_to_percent(3, 0, 0) == pytest.approx(3.0)
    assert lsd_to_percent(3) == pytest.approx(3.0)


def test_shilling_is_one_twentieth():
    assert lsd_to_percent(0, 10, 0) == pytest.approx(0.5)


def test_penny_is_one_240th():
    assert lsd_to_percent(0, 0, 6) == pytest.approx(0.025)


def test_all_none_is_not_quoted():
    assert lsd_to_percent(None, None, None) is None


def test_partial_none_treated_as_zero():
    assert lsd_to_percent(4, None, None) == pytest.approx(4.0)


def test_out_of_range_shillings_raise():
    with pytest.raises(ValueError):
        lsd_to_percent(4, 25, 0)


def test_out_of_range_pence_raise():
    with pytest.raises(ValueError):
        lsd_to_percent(4, 3, 15)


@pytest.mark.parametrize(
    "raw,expected",
    [("4", 4.0), (" 3 ", 3.0), ("£5", 5.0), ("6%", 6.0), ("", None),
     ("—", None), ("nil", None), ("garbage", None), (None, None)],
)
def test_parse_number(raw, expected):
    got = parse_number(raw)
    if expected is None:
        assert got is None
    else:
        assert got == pytest.approx(expected)


def test_cells_to_percent_end_to_end():
    assert cells_to_percent("4", "3", "6") == pytest.approx(4.175)
    assert cells_to_percent("", "", "") is None
