from pari_mutuel_trader.data.odds_log import append_odds_snapshot, load_odds_panel


def _events():
    return [
        {"event": "IRAN_HORMUZ", "kalshi_ticker": "KX", "prob": 0.62, "prob_source": "kalshi_live",
         "premium": 0.41, "premium_source": "vol:^OVX", "resolution_state": "active", "resolution_decay": 1.0},
        {"event": "REARM", "prob": 0.70, "premium": 0.40},  # no ticker; static
    ]


def test_appends_one_row_per_event(tmp_path):
    p = tmp_path / "panel.csv"
    n = append_odds_snapshot(_events(), str(p), "2026-02-24")
    assert n == 2
    df = load_odds_panel(str(p))
    assert len(df) == 2
    assert set(df["event"]) == {"IRAN_HORMUZ", "REARM"}
    assert float(df[df["event"] == "IRAN_HORMUZ"]["prob"].iloc[0]) == 0.62


def test_same_day_append_is_idempotent(tmp_path):
    p = tmp_path / "panel.csv"
    append_odds_snapshot(_events(), str(p), "2026-02-24")
    n2 = append_odds_snapshot(_events(), str(p), "2026-02-24")  # re-run same day
    assert n2 == 0
    assert len(load_odds_panel(str(p))) == 2


def test_new_day_extends_panel(tmp_path):
    p = tmp_path / "panel.csv"
    append_odds_snapshot(_events(), str(p), "2026-02-24")
    n = append_odds_snapshot(_events(), str(p), "2026-03-03")
    assert n == 2
    df = load_odds_panel(str(p))
    assert len(df) == 4
    assert df["date"].nunique() == 2


def test_missing_path_is_noop(tmp_path):
    assert append_odds_snapshot(_events(), None, "2026-02-24") == 0


def test_load_missing_returns_empty(tmp_path):
    df = load_odds_panel(str(tmp_path / "nope.csv"))
    assert df.empty
