"""Rigobon-Sack under neutral bases + the neutral placebo.

Pins: Berlin's premium is robust across the London and Swiss bases and clearly
exceeds the neutral floor; the neutrals themselves carry premia of ~0.09-0.12
(so the premium is not cleanly war risk). Runs on the mirrored short rates.
"""

import os

import pytest

from neal_weidenmier.load import load_short_rates, to_series_map
from war_premia.run import run_crisis
from war_premia.warweeks import get_crisis

SHORT = os.path.join(os.path.dirname(__file__), "..", "..", "neal_weidenmier",
                     "data", "stinterestrates.xls")

pytestmark = pytest.mark.skipif(
    not os.path.exists(SHORT), reason="mirrored short-rate workbook not present"
)


def _betas(basis_key):
    smap = to_series_map(load_short_rates(SHORT))
    return {r.city: r for r in run_crisis(smap, get_crisis("full"), basis_key=basis_key)}


def test_berlin_premium_survives_a_swiss_basis():
    london = _betas("london_trade3mo")
    swiss = _betas("geneva_market")
    assert london["berlin_openmkt"].single.beta > 0.25
    assert swiss["berlin_openmkt"].single.beta > 0.25   # robust, not a London artifact


def test_neutrals_carry_a_premium_so_it_is_not_cleanly_war_risk():
    res = _betas("london_trade3mo")
    # genuine neutrals show premia of the same size as Paris/Vienna
    for slug in ("amsterdam_openmkt", "geneva_market", "stockholm_market"):
        assert res[slug].single.beta > 0.05
    # and Berlin clearly exceeds that neutral floor
    neutral_floor = max(res[s].single.beta for s in
                        ("amsterdam_openmkt", "geneva_market", "stockholm_market"))
    assert res["berlin_openmkt"].single.beta > neutral_floor + 0.1
