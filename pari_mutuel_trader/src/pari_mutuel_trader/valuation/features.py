from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from pari_mutuel_trader.valuation.intrinsic import ValuationInputs, intrinsic_value
from pari_mutuel_trader.valuation.quality import QualityProfile
from pari_mutuel_trader.valuation.sell_rules import SellPolicy

VALUATION_COLUMNS = ("iv15", "iv8", "discount_to_iv15", "premium_to_iv8", "durability", "dislocation")


@dataclass
class Revision:
    """One dated set of assumptions about a business."""

    as_of: date | None
    inputs: ValuationInputs


def _as_date(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def _inputs_from(row: dict) -> ValuationInputs:
    fade = row.get("fade_years")
    terminal = row.get("terminal_growth")
    return ValuationInputs(
        owner_earnings_ps=float(row["owner_earnings_ps"]),
        growth=float(row.get("growth", 0.08)),
        quality=QualityProfile(
            moat=float(row.get("moat", 0.5)),
            roic=float(row.get("roic", 0.12)),
            roic_stability=float(row.get("roic_stability", 0.5)),
            wacc=float(row.get("wacc", 0.08)),
        ),
        fade_years=int(fade) if fade else None,
        terminal_growth=float(terminal) if terminal is not None else None,
    )


def load_fundamentals(path: str) -> dict[str, list[Revision]]:
    """Per-symbol assumptions, optionally as a dated series of revisions.

    A symbol maps either to one set of assumptions or to a list carrying `as_of`
    dates. Revisions are what let the sleeve tell a dislocation from a
    deterioration: if the estimate of value fell as far as the price did, the
    business changed and the discount is not an opportunity.
    """
    import yaml

    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    entries = raw.get("fundamentals", raw)
    out: dict[str, list[Revision]] = {}
    for symbol, value in entries.items():
        rows = value if isinstance(value, list) else [value]
        revisions = [Revision(_as_date(r.get("as_of")), _inputs_from(r)) for r in rows]
        out[str(symbol)] = sorted(revisions, key=lambda r: r.as_of or date.min)
    return out


def _revision_frame(revisions: list[Revision], policy: SellPolicy) -> pd.DataFrame:
    """IV15/IV8/durability per revision, indexed by the date it took effect."""
    rows = []
    for rev in revisions:
        rows.append({
            "as_of": pd.Timestamp(rev.as_of) if rev.as_of else pd.Timestamp.min,
            "iv15": intrinsic_value(rev.inputs, policy.required_return),
            "iv8": intrinsic_value(rev.inputs, policy.hold_return),
            "durability": rev.inputs.quality.durability(),
        })
    return pd.DataFrame(rows).set_index("as_of").sort_index()


def valuation_columns(
    features: pd.DataFrame,
    fundamentals: dict[str, list[Revision]],
    policy: SellPolicy | None = None,
    dislocation_window: int = 60,
) -> pd.DataFrame:
    """IV columns aligned to a (date, symbol) feature frame.

    `dislocation` is the price fall in excess of the fall in value over the window.
    A price that dropped alongside its own intrinsic value is not dislocated - the
    business got worse - and scores zero.
    """
    policy = policy or SellPolicy()
    dates = features.index.get_level_values("date")
    symbols = features.index.get_level_values("symbol")

    pieces = []
    for symbol in sorted(set(symbols) & set(fundamentals)):
        mask = symbols == symbol
        symbol_dates = pd.DatetimeIndex(dates[mask]).sort_values().unique()
        revisions = _revision_frame(fundamentals[symbol], policy)
        aligned = revisions.reindex(revisions.index.union(symbol_dates)).ffill().reindex(symbol_dates)
        aligned.index.name = "date"
        aligned["symbol"] = symbol
        pieces.append(aligned.reset_index().set_index(["date", "symbol"]))

    if not pieces:
        return pd.DataFrame(index=features.index, columns=list(VALUATION_COLUMNS), dtype=float).fillna(0.0)

    valued = pd.concat(pieces).reindex(features.index)
    price = features["close"]
    valued["discount_to_iv15"] = valued["iv15"] / price - 1.0
    valued["premium_to_iv8"] = price / valued["iv8"] - 1.0

    grouped = valued.groupby(level="symbol")
    value_change = grouped["iv15"].pct_change(dislocation_window)
    price_change = price.groupby(level="symbol").pct_change(dislocation_window)
    valued["dislocation"] = (value_change - price_change).clip(lower=0.0)

    return valued[list(VALUATION_COLUMNS)].fillna(0.0)


def attach_valuation(
    features: pd.DataFrame,
    fundamentals: dict[str, list[Revision]],
    policy: SellPolicy | None = None,
    dislocation_window: int = 60,
) -> pd.DataFrame:
    """Return the feature frame with the valuation columns filled in."""
    columns = valuation_columns(features, fundamentals, policy, dislocation_window)
    out = features.copy()
    for name in VALUATION_COLUMNS:
        out[name] = columns[name]
    return out
