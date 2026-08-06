import pytest

from gallica_le_temps.config import RunConfig, config_from_dict, load_config


def _base_dict():
    return {
        "date_start": "1914-07-27",
        "date_end": "1914-07-29",
        "min_ocr_quality": 80,
        "targets": [
            {"name": "rente_3pct", "anchors": ["3 0/0", "3 %"], "page": 3},
            {"name": "bdf", "anchors": "Banque de France", "page": 3},
        ],
    }


def test_config_from_dict_parses_targets():
    cfg = config_from_dict(_base_dict())
    assert isinstance(cfg, RunConfig)
    assert len(cfg.targets) == 2
    # A string anchor is normalised to a one-element list.
    assert cfg.targets[1].anchors == ["Banque de France"]


def test_dates_inclusive_range():
    cfg = config_from_dict(_base_dict())
    assert cfg.dates() == ["1914-07-27", "1914-07-28", "1914-07-29"]


def test_reversed_range_raises():
    d = _base_dict()
    d["date_start"], d["date_end"] = d["date_end"], d["date_start"]
    with pytest.raises(ValueError):
        config_from_dict(d).dates()


def test_target_requires_anchor():
    with pytest.raises(ValueError):
        config_from_dict(
            {"date_start": "1914-07-27", "date_end": "1914-07-27",
             "targets": [{"name": "x", "anchors": []}]}
        )


def test_config_requires_targets():
    with pytest.raises(ValueError):
        config_from_dict({"date_start": "1914-07-27", "date_end": "1914-07-27"})


def test_min_ocr_quality_null_disables():
    d = _base_dict()
    d["min_ocr_quality"] = None
    assert config_from_dict(d).min_ocr_quality is None


def test_load_config_from_yaml(tmp_path):
    import yaml

    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.safe_dump(_base_dict()), encoding="utf-8")
    cfg = load_config(str(p))
    assert cfg.date_start == "1914-07-27"
    assert cfg.targets[0].name == "rente_3pct"
