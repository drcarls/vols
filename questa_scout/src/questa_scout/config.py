from __future__ import annotations

import os
from pathlib import Path


def load_yaml(path: str) -> dict:
    import yaml

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def fixtures_dir() -> Path:
    return project_root() / "fixtures"


def brightdata_token() -> str | None:
    """Read the Bright Data API token from the environment.

    Never hard-code or commit this. Set BRIGHTDATA_API_TOKEN in the
    environment (or a local, git-ignored .env) before running live.
    """
    return os.environ.get("BRIGHTDATA_API_TOKEN")


def brightdata_zone() -> str:
    """Bright Data zone name. Account-specific -- a dedicated SERP zone, or a
    Web Unlocker zone (which also returns SERP JSON via brd_json). Set
    BRIGHTDATA_ZONE to match your account; defaults to 'serp'."""
    return os.environ.get("BRIGHTDATA_ZONE", "serp")
