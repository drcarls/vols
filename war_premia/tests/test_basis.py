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


def test_london_itself_is_belligerent_grade_war_sensitive():
    # London (the paper's basis) carries a large premium vs neutral bases -- as big
    # as Berlin -- so it is not a war-neutral reference.
    swiss = _betas("geneva_market")
    swede = _betas("stockholm_market")
    lon = max(swiss["london_trade3mo"].single.beta, swede["london_trade3mo"].single.beta)
    assert lon > 0.2                                   # London is strongly war-sensitive
    assert lon >= swiss["berlin_openmkt"].single.beta - 0.05   # comparable to Berlin
    # asymmetry: neutrals show only ~0.10 against London, London shows >0.2 vs them
    neutral_vs_london = _betas("london_trade3mo")["stockholm_market"].single.beta
    assert lon > neutral_vs_london + 0.1


def test_per_conflict_estimates_are_not_robust_but_full_sample_germany_is():
    from war_premia.warweeks import CRISES
    cr = {c.key: c for c in CRISES}
    # Full-sample Germany is robust across London/Swiss/Swedish (>0.2), Amsterdam aside.
    full_swiss = _betas("geneva_market")
    full_swede = _betas("stockholm_market")
    assert full_swiss["berlin_openmkt"].single.beta > 0.2
    assert full_swede["berlin_openmkt"].single.beta > 0.2
    # A small-n crisis (Agadir, n=22) is NOT robust: the London vs Amsterdam Germany
    # premium differs by more than a full point (noise).
    from neal_weidenmier.load import load_short_rates, to_series_map
    from war_premia.run import run_crisis
    smap = to_series_map(load_short_rates(SHORT))
    ag = cr["morocco2"]
    lon = {r.city: r for r in run_crisis(smap, ag, basis_key="london_trade3mo")}
    ams = {r.city: r for r in run_crisis(smap, ag, basis_key="amsterdam_openmkt")}
    assert abs(lon["berlin_openmkt"].single.beta - ams["berlin_openmkt"].single.beta) > 1.0


def test_neutral_floor_is_pooled_not_per_crisis_and_can_beat_a_belligerent():
    from war_premia.warweeks import CRISES
    from neal_weidenmier.load import load_short_rates, to_series_map
    from war_premia.run import run_crisis
    cr = {c.key: c for c in CRISES}
    smap = to_series_map(load_short_rates(SHORT))
    balk = {r.city: r for r in run_crisis(smap, cr["balkans"], basis_key="london_trade3mo")}
    bos = {r.city: r for r in run_crisis(smap, cr["bosnia"], basis_key="london_trade3mo")}
    # Stockholm's pooled floor is NOT stable per crisis: negative in Bosnia...
    assert bos["stockholm_market"].single.beta < 0
    # ...and in the Balkans neutral Stockholm outscores belligerent Berlin.
    assert balk["stockholm_market"].single.beta > balk["berlin_openmkt"].single.beta


def test_berlin_significant_only_pooled_and_neutrals_significant_too():
    from war_premia.warweeks import CRISES
    from neal_weidenmier.load import load_short_rates, to_series_map
    from war_premia.run import run_crisis
    cr = {c.key: c for c in CRISES}
    smap = to_series_map(load_short_rates(SHORT))
    per = {k: {r.city: r for r in run_crisis(smap, cr[k], basis_key="london_trade3mo")}
           for k in ("morocco1", "bosnia", "balkans", "full")}
    # Berlin is NOT significant in any individual crisis (|t| < 2) ...
    for k in ("morocco1", "bosnia", "balkans"):
        assert abs(per[k]["berlin_openmkt"].single.t_stat) < 2.0
    # ... but is strongly significant pooled, and neutrals are significant pooled too.
    assert per["full"]["berlin_openmkt"].single.t_stat > 4.0
    assert per["full"]["copenhagen_market"].single.t_stat > 3.0
    assert per["full"]["stockholm_market"].single.t_stat > 3.0
