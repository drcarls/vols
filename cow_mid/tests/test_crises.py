"""Crisis->dispute mapping and crisis_lag event emission."""

import datetime

from cow_mid.crises import build_events, unmapped
from cow_mid.parse import Dispute


def _disputes():
    D = datetime.date
    return {
        "30": Dispute("30", D(1908, 10, 6), D(1909, 3, 1), 4, None, [345], [300]),
        "315": Dispute("315", D(1911, 7, 1), D(1911, 10, 1), 3, 0, [255], [220, 200]),
        "21": Dispute("21", D(1912, 11, 21), D(1912, 12, 1), 3, 0, [300], [365, 345]),
        "257": Dispute("257", D(1914, 7, 23), D(1918, 11, 11), 5, 6, [300, 255], [345, 365]),
    }


def test_events_use_objective_onsets():
    events = build_events(_disputes())
    by = {e["name"]: e for e in events}
    assert by["Agadir_1911"]["onset"] == "1911-07-01"
    assert by["Bosnia_1908"]["onset"] == "1908-10-06"
    assert by["Balkans_1912_13"]["onset"] == "1912-11-21"   # objective, != 10-08
    assert by["July_1914"]["onset"] == "1914-07-23"


def test_series_assignment_and_july_censored():
    by = {e["name"]: e for e in build_events(_disputes())}
    assert by["Agadir_1911"]["series"] == "germany"
    assert by["Balkans_1912_13"]["series"] == "austria_hungary"
    assert by["July_1914"].get("measurable") is False
    assert by["July_1914"]["decision_window_days"] == 5


def test_notes_carry_hostility_and_participants():
    by = {e["name"]: e for e in build_events(_disputes())}
    assert "war" in by["July_1914"]["notes"]
    assert "display of force" in by["Agadir_1911"]["notes"]


def test_morocco_1905_is_an_unmapped_gap():
    events = build_events(_disputes())
    assert "Morocco_1905" not in {e["name"] for e in events}
    assert "Morocco_1905" in unmapped(_disputes())
