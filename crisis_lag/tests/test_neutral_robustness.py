"""The per-country cause-or-cover signal is not robust to the neutral benchmark.

Pins: France is calm in the money market against EVERY neutral (robust null);
Russia scatters widely across neutrals (not robust). Skips if data absent.
"""

import os

import pytest

import neutral_robustness as nr

pytestmark = pytest.mark.skipif(
    not (os.path.exists(nr.SHORT) and os.path.exists(nr.BONDS)),
    reason="mirrored workbooks not present",
)


def test_france_money_market_is_calm_against_every_neutral():
    mm = nr.money_market_table(180)
    for neutral, row in mm.items():
        assert row["Morocco/Fr"] is not None and row["Morocco/Fr"] <= 30, neutral


def test_russia_signal_scatters_across_neutrals():
    mm = nr.money_market_table(180)
    ru = [row["Bosnia/Ru"] for row in mm.values() if row["Bosnia/Ru"] is not None]
    assert max(ru) - min(ru) >= 40   # e.g. ~21 (US) to ~89 (Sweden): not robust


def test_austria_bond_repricing_holds_across_bond_neutrals():
    bt = nr.bond_table(270)
    au = [row["Balkans/Au"] for row in bt.values() if row["Balkans/Au"] is not None]
    assert min(au) >= 80             # high vs Dutch, US, Italian alike
