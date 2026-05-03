from __future__ import annotations

from pathlib import Path


def load_yaml(path: str) -> dict:
    import yaml

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]
