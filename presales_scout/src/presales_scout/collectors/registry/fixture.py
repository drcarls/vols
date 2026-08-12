from __future__ import annotations

"""Offline registry backend — a bundled sample export, no network or key.

Delegates to CsvExportBackend over fixtures/registry/sample_export.csv so the
whole harvest -> discover pipeline runs offline and the real CSV parser is
exercised in tests.
"""

from pathlib import Path

from .csv_export import CsvExportBackend

_DEFAULT = Path(__file__).resolve().parents[4] / "fixtures" / "registry" / "sample_export.csv"


class FixtureBackend(CsvExportBackend):
    def __init__(self, export_path: str | Path | None = None):
        super().__init__(export_path or _DEFAULT)
