from crisis_lag.events import DEFAULT_EVENTS, event_from_dict, load_events


def test_default_events_cover_the_five_crises_plus_1914():
    names = [e.name for e in DEFAULT_EVENTS]
    assert names == [
        "Morocco_1905", "Bosnia_1908", "Agadir_1911", "Balkans_1912_13", "July_1914",
    ]


def test_july_1914_is_censored_with_short_window():
    july = next(e for e in DEFAULT_EVENTS if e.name == "July_1914")
    assert july.measurable is False
    assert july.decision_window_days == 5
    assert july.onset == "1914-07-23"  # Austrian ultimatum


def test_onset_dates_parse():
    for e in DEFAULT_EVENTS:
        assert e.onset_date().isoformat() == e.onset


def test_event_from_dict_defaults():
    e = event_from_dict({"name": "x", "onset": "1911-07-01", "series": "germany"})
    assert e.measurable is True
    assert e.baseline_start_days == 120
    assert e.search_days == 180


def test_load_events_yaml(tmp_path):
    import yaml

    p = tmp_path / "events.yaml"
    p.write_text(
        yaml.safe_dump({"events": [
            {"name": "Agadir", "onset": "1911-07-01", "series": "germany"},
            {"name": "July_1914", "onset": "1914-07-23", "series": "austria_hungary",
             "measurable": False, "decision_window_days": 5},
        ]}),
        encoding="utf-8",
    )
    events = load_events(str(p))
    assert len(events) == 2
    assert events[1].measurable is False
