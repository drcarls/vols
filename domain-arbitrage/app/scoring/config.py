"""Loader for the versioned scoring configuration.

The YAML in ``config/`` is the single source of truth for every weight, prior
and threshold in the model. Nothing in ``app/scoring`` may hard-code a magic
number that influences a score; if you need a constant, put it in the YAML with
a rationale so it shows up in review and can be swept later.

``ScoringConfig.version`` is stamped onto every persisted score so that a
prediction made months ago can be reproduced exactly.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


class ScoringConfig:
    """Thin, dict-backed view over the YAML with helpers for interpolation."""

    def __init__(self, raw: dict[str, Any], path: Path | None = None) -> None:
        self.raw = raw
        self.path = path
        self._digest = hashlib.sha256(
            yaml.safe_dump(raw, sort_keys=True).encode()
        ).hexdigest()[:12]

    # -- identity -----------------------------------------------------------
    @property
    def version(self) -> str:
        return str(self.raw["meta"]["version"])

    @property
    def calibrated(self) -> bool:
        return bool(self.raw["meta"].get("calibrated", False))

    @property
    def calibration_note(self) -> str:
        return str(self.raw["meta"].get("calibration_note", ""))

    @property
    def digest(self) -> str:
        """Short content hash. Distinguishes edits made without a version bump."""
        return self._digest

    @property
    def stamp(self) -> str:
        return f"{self.version}+{self._digest}"

    # -- access -------------------------------------------------------------
    def section(self, name: str) -> dict[str, Any]:
        return self.raw[name]

    def get(self, path: str, default: Any = None) -> Any:
        """Dotted lookup: ``cfg.get('valuation.wholesale_ratio_of_retail')``."""
        node: Any = self.raw
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def tld_value(self, path: str, tld: str, default_key: str = "_default") -> Any:
        table = self.get(path) or {}
        if tld in table:
            return table[tld]
        return table.get(default_key)

    # -- numeric helpers ----------------------------------------------------
    @staticmethod
    def interpolate_table(table: dict[Any, float], x: float) -> float:
        """Piecewise-linear interpolation over a {breakpoint: value} table.

        Flat outside the range. Used for the length and buyer-depth ladders so
        the curves stay visible in the config rather than buried in code.
        """
        pts = sorted((float(k), float(v)) for k, v in table.items())
        if not pts:
            return 1.0
        if x <= pts[0][0]:
            return pts[0][1]
        if x >= pts[-1][0]:
            return pts[-1][1]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if x0 <= x <= x1:
                if x1 == x0:
                    return y1
                t = (x - x0) / (x1 - x0)
                return y0 + t * (y1 - y0)
        return pts[-1][1]

    @staticmethod
    def lerp(lo: float, hi: float, t: float) -> float:
        """Linear blend with ``t`` clamped to [0, 1]."""
        t = min(1.0, max(0.0, t))
        return lo + (hi - lo) * t

    def validate(self) -> list[str]:
        """Return a list of configuration problems (empty means healthy)."""
        problems: list[str] = []
        weights = self.get("opportunity.weights") or {}
        total = sum(float(v) for v in weights.values())
        if abs(total - 1.0) > 1e-6:
            problems.append(f"opportunity.weights sum to {total:.6f}, expected 1.0")
        for key in ("valuation", "probability", "economics", "opportunity",
                    "recommendation", "portfolio"):
            if key not in self.raw:
                problems.append(f"missing required section: {key}")
        base = self.get("probability.base_annual_sell_through")
        if base is None or not (0 < float(base) < 1):
            problems.append("probability.base_annual_sell_through must be in (0, 1)")
        return problems


def load_scoring_config(path: Path) -> ScoringConfig:
    raw = yaml.safe_load(Path(path).read_text())
    cfg = ScoringConfig(raw, Path(path))
    problems = cfg.validate()
    if problems:
        raise ValueError("Invalid scoring config: " + "; ".join(problems))
    return cfg


@lru_cache
def get_scoring_config(path: str | None = None) -> ScoringConfig:
    from app.config import get_settings

    resolved = Path(path) if path else get_settings().scoring_config_path
    return load_scoring_config(resolved)


def with_overrides(cfg: ScoringConfig, overrides: dict[str, Any],
                   *, label: str | None = None) -> ScoringConfig:
    """Return a copy of ``cfg`` with dotted-path values replaced.

    Used by the sensitivity harness to build config variants without touching
    the YAML on disk. The copy is deep, so a variant can never leak back into
    the shared configuration.

    ``label`` is recorded under ``meta.variant_label`` so a variant's identity
    travels with it, and the content digest changes with every override - two
    variants can never be confused for one another.
    """
    import copy

    raw = copy.deepcopy(cfg.raw)
    for path, value in overrides.items():
        parts = path.split(".")
        node = raw
        for part in parts[:-1]:
            if part not in node or not isinstance(node[part], dict):
                raise KeyError(f"no such config section: {path!r}")
            node = node[part]
        if parts[-1] not in node:
            raise KeyError(f"no such config key: {path!r}")
        node[parts[-1]] = value
    if label:
        raw.setdefault("meta", {})["variant_label"] = label
    return ScoringConfig(raw, cfg.path)


def renormalised_weights(cfg: ScoringConfig, component: str,
                         weight: float) -> dict[str, float]:
    """Set one opportunity weight and rescale the rest to keep the sum at 1.0.

    Rescaling proportionally rather than uniformly means the *relative* standing
    of the untouched components is preserved, so a sweep over one weight
    measures that weight's effect and nothing else.
    """
    weights = dict(cfg.get("opportunity.weights"))
    if component not in weights:
        raise KeyError(f"unknown opportunity component: {component!r}")
    if not 0.0 <= weight <= 1.0:
        raise ValueError("weight must be in [0, 1]")

    others = {k: v for k, v in weights.items() if k != component}
    others_total = sum(others.values())
    if others_total <= 0:
        raise ValueError("cannot rescale: all other weights are zero")

    scale = (1.0 - weight) / others_total
    out = {k: round(v * scale, 6) for k, v in others.items()}
    out[component] = round(weight, 6)

    # Absorb float drift into the largest untouched component so the sum is
    # exactly 1.0 and ScoringConfig.validate() passes.
    drift = 1.0 - sum(out.values())
    if abs(drift) > 1e-12 and others:
        largest = max(others, key=lambda k: out[k])
        out[largest] = round(out[largest] + drift, 12)
    return out
