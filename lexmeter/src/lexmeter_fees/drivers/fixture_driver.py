"""Offline driver that reads local HTML fixtures.

Exists so the full capture contract -- policy enforcement, artifact storage,
carry-forward, metrics, flags -- can be exercised end to end with no network and
no live sites. Test doubles that stop at the boundary tend to hide exactly the
bugs that matter here, such as a fee's first-seen step index drifting as it is
restated on later pages.

Fixtures annotate the values of interest with ``data-lex`` attributes, so the
driver stays a few lines of parsing rather than a second extraction engine.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..capture import PageReading
from ..extract import RawFeeRow
from ..model import StepKind

_HEADLINE = re.compile(r'data-lex="headline"[^>]*>([^<]*)<', re.IGNORECASE)
_TOTAL = re.compile(r'data-lex="total"[^>]*>([^<]*)<', re.IGNORECASE)
_FEE = re.compile(r"<[^>]*data-lex=\"fee\"[^>]*>", re.IGNORECASE)
_ATTR = re.compile(r'data-(?P<key>label|amount|removable|purpose|nearby)="(?P<val>[^"]*)"')


def _first(pattern: re.Pattern[str], html: str) -> str | None:
    match = pattern.search(html)
    return match.group(1).strip() if match else None


def _fee_rows(html: str) -> list[RawFeeRow]:
    rows: list[RawFeeRow] = []
    for tag in _FEE.findall(html):
        attrs = {m.group("key"): m.group("val") for m in _ATTR.finditer(tag)}
        removable = attrs.get("removable")
        rows.append(
            RawFeeRow(
                label=attrs.get("label", ""),
                amount_text=attrs.get("amount", ""),
                removable=(
                    None if removable in (None, "", "unknown") else removable == "true"
                ),
                purpose_text=attrs.get("purpose") or None,
                nearby_text=attrs.get("nearby") or None,
            )
        )
    return rows


class FixtureDriver:
    """Serves a scripted flow from a directory of fixture pages."""

    def __init__(self, root: Path | str, status: int = 200) -> None:
        self.root = Path(root)
        self.status = status
        self.closed = False

    def read(self, step_kind: StepKind, action: str | None) -> PageReading:
        if action is None:
            raise ValueError("FixtureDriver needs a fixture filename as the action")
        path = self.root / action
        html = path.read_text()
        return PageReading(
            url=f"file://{path}",
            status=self.status,
            body_text=html,
            headline_text=_first(_HEADLINE, html),
            total_text=_first(_TOTAL, html),
            fee_rows=_fee_rows(html),
            screenshot=b"\x89PNG\r\n\x1a\n" + html.encode()[:64],  # deterministic stand-in
            dom=html.encode(),
            scroll_y=0,
        )

    def close(self) -> None:
        self.closed = True


class BlockingDriver:
    """Returns a block signal, to exercise the record-and-abort path."""

    def __init__(self, status: int = 429, body: str = "", after_steps: int = 0) -> None:
        self.status = status
        self.body = body
        self.after_steps = after_steps
        self._calls = 0
        self.closed = False

    def read(self, step_kind: StepKind, action: str | None) -> PageReading:
        self._calls += 1
        blocked = self._calls > self.after_steps
        return PageReading(
            url="https://example.test/step",
            status=self.status if blocked else 200,
            body_text=self.body if blocked else "<html></html>",
            headline_text="$50.00",
            total_text=None,
            fee_rows=[],
        )

    def close(self) -> None:
        self.closed = True
