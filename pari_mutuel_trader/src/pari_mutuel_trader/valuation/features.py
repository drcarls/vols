from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from pari_mutuel_trader.valuation.intrinsic import ValuationInputs, intrinsic_value
from pari_mutuel_trader.valuation.quality import QualityProfile
from pari_mutuel_trader.valuation.sell_rules import SellPolicy

# One model, read at several hurdle rates. These are not independent opinions:
# IV6 > IV8 > IV15 always, and their cross-sectional ranks correlate ~0.99.
HURDLES = {"iv6": 0.06, "iv8": 0.08, "iv15": 0.15}
IV_CHANGE_WINDOWS = {"1m": 21, "3m": 63, "6m": 126}

VALUATION_COLUMNS = (
    "iv6", "iv8", "iv15",
    "discount_to_iv6", "discount_to_iv8", "discount_to_iv15",
    "premium_to_iv8",
    "iv_consensus", "iv_dispersion", "iv_agreement",
    "iv6_chg_1m", "iv6_chg_3m", "iv6_chg_6m",
    "iv8_chg_1m", "iv8_chg_3m", "iv8_chg_6m",
    "durability", "dislocation",
)


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


def _revision_frame(revisions: list[Revision], publication_lag_days: int = 0) -> pd.DataFrame:
    """IV per hurdle rate and durability, indexed by the date the figures were usable.

    `publication_lag_days` pushes each revision forward from the period it describes
    to the date it could actually have been read. Fundamentals dated to a period end
    but applied from that date are the commonest lookahead in a valuation backtest.
    """
    rows = []
    for rev in revisions:
        stamp = pd.Timestamp(rev.as_of) if rev.as_of else pd.Timestamp.min
        if rev.as_of and publication_lag_days:
            stamp = stamp + pd.Timedelta(days=publication_lag_days)
        row = {"as_of": stamp, "durability": rev.inputs.quality.durability()}
        for name, hurdle in HURDLES.items():
            row[name] = intrinsic_value(rev.inputs, hurdle)
        rows.append(row)
    return pd.DataFrame(rows).set_index("as_of").sort_index()


def valuation_columns(
    features: pd.DataFrame,
    fundamentals: dict[str, list[Revision]],
    policy: SellPolicy | None = None,
    dislocation_window: int = 60,
    publication_lag_days: int = 0,
) -> pd.DataFrame:
    """IV columns aligned to a (date, symbol) feature frame.

    Everything here is backward-looking by construction: a revision applies only
    from its own date (plus any publication lag) onward, and every change column is
    a trailing difference. Nothing reads a price or a fundamental from the future.
    """
    policy = policy or SellPolicy()
    dates = features.index.get_level_values("date")
    symbols = features.index.get_level_values("symbol")

    pieces = []
    for symbol in sorted(set(symbols) & set(fundamentals)):
        mask = symbols == symbol
        symbol_dates = pd.DatetimeIndex(dates[mask]).sort_values().unique()
        revisions = _revision_frame(fundamentals[symbol], publication_lag_days)
        aligned = revisions.reindex(revisions.index.union(symbol_dates)).ffill().reindex(symbol_dates)
        aligned.index.name = "date"
        aligned["symbol"] = symbol
        pieces.append(aligned.reset_index().set_index(["date", "symbol"]))

    if not pieces:
        return pd.DataFrame(index=features.index, columns=list(VALUATION_COLUMNS), dtype=float).fillna(0.0)

    valued = pd.concat(pieces).reindex(features.index)
    price = features["close"]

    for name in HURDLES:
        valued[f"discount_to_{name}"] = valued[name] / price - 1.0
    valued["premium_to_iv8"] = price / valued["iv8"] - 1.0

    # IV6 and IV8 are the same model at two hurdle rates, so "agreement" between
    # them is not two opinions converging. The spread between them is a duration
    # measure: it widens when more of the value sits in distant cash flows.
    valued["iv_consensus"] = 0.5 * (valued["discount_to_iv6"] + valued["discount_to_iv8"])
    valued["iv_dispersion"] = (valued["iv6"] - valued["iv8"]).abs() / price

    grouped = valued.groupby(level="symbol")
    for name in ("iv6", "iv8"):
        for label, window in IV_CHANGE_WINDOWS.items():
            valued[f"{name}_chg_{label}"] = grouped[name].pct_change(window)

    value_change = grouped["iv15"].pct_change(dislocation_window)
    price_change = price.groupby(level="symbol").pct_change(dislocation_window)
    valued["dislocation"] = (value_change - price_change).clip(lower=0.0)

    valued["iv_agreement"] = _agreement(valued)
    return valued[list(VALUATION_COLUMNS)].fillna(0.0)


def _agreement(valued: pd.DataFrame) -> pd.Series:
    """Whether the 6% and 8% readings put a name in the same third of the universe.

    Kept because it was asked for, but expect it to be almost always "agree": the
    two readings are monotone transforms of one another.
    """
    def label(frame: pd.DataFrame) -> pd.Series:
        out = pd.Series("neutral", index=frame.index, dtype=object)
        for name in ("discount_to_iv6", "discount_to_iv8"):
            ranked = frame[name].rank(pct=True)
            frame = frame.assign(**{f"_{name}": pd.cut(ranked, [0, 1 / 3, 2 / 3, 1.0],
                                                       labels=["expensive", "neutral", "cheap"],
                                                       include_lowest=True)})
        same = frame["_discount_to_iv6"].astype(str) == frame["_discount_to_iv8"].astype(str)
        out[same] = frame.loc[same, "_discount_to_iv6"].astype(str)
        out[~same] = "disagree"
        return out

    pieces = [label(group) for _, group in valued.groupby(level="date")]
    if not pieces:
        return pd.Series("neutral", index=valued.index, dtype=object)
    return pd.concat(pieces).reindex(valued.index)


def attach_valuation(
    features: pd.DataFrame,
    fundamentals: dict[str, list[Revision]],
    policy: SellPolicy | None = None,
    dislocation_window: int = 60,
    publication_lag_days: int = 0,
) -> pd.DataFrame:
    """Return the feature frame with the valuation columns filled in."""
    columns = valuation_columns(features, fundamentals, policy, dislocation_window, publication_lag_days)
    out = features.copy()
    for name in VALUATION_COLUMNS:
        out[name] = columns[name]
    return out
