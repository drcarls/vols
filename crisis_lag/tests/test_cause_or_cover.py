"""Pin the cause-or-cover timing test — what the market data can/can't say.

Asserts the asymmetric finding: no crisis shows stress becoming material only
AFTER the climb-down (so no support for pure 'cover'); Russia and Austria are
materially stressed well before; France's OWN yield shows no material stress
(the case that leans toward the objection). Skips if the workbook is absent.
"""

import datetime
import os

import pytest

import cause_or_cover as cc

BONDS = os.path.join(os.path.dirname(__file__), "..", "..", "neal_weidenmier",
                     "data", "longtermbonds.xls")

pytestmark = pytest.mark.skipif(
    not os.path.exists(BONDS) or not os.path.exists(cc.SPREADS),
    reason="mirrored workbook / built spreads not present",
)


def test_no_crisis_has_stress_only_after_climbdown():
    # The refuting pattern (pure 'cover') appears in neither measure.
    for path in (cc.SPREADS, cc.YIELDS):
        for c, mat, cd, gap, verdict in cc.run(path):
            if mat is not None:
                assert mat <= cd, f"{c.crisis} on {path}: material {mat} after climb-down {cd}"


def test_russia_and_austria_materially_stressed_before_climbdown():
    rows = {c.crisis: (mat, cd) for c, mat, cd, gap, v in cc.run(cc.SPREADS)}
    for name in ("Bosnia_1909", "Balkans_1912_13"):
        mat, cd = rows[name]
        assert mat is not None and mat < cd


def test_france_own_yield_shows_no_material_stress_in_1905():
    # Morocco/France on RAW yield: France's own borrowing cost never crosses z>2
    # -> French finances were not the binding constraint (leans to the objection).
    rows = {c.crisis: mat for c, mat, cd, gap, v in cc.run(cc.YIELDS)}
    assert rows["Morocco_1905"] is None
