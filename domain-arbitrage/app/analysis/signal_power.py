"""Does buyer depth actually predict resale?

This module exists to answer the question the whole project is built around,
and to answer it honestly - including "not yet, there is not enough data",
which is the answer it will give for a long time.

Method, deliberately simple:

  * Take resolved paper positions (a sale/no-sale outcome is known).
  * For each registered signal, read the value frozen on the position at
    prediction time - not today's recomputed value.
  * Report rank correlation with the binary sale outcome, plus the difference
    in mean signal between sold and unsold, plus an AUC.

Why rank correlation and AUC rather than a fitted model: with a few dozen
outcomes, fitting anything with interactions would produce a confident-looking
number with no information in it. Rank statistics degrade gracefully on small
samples and are hard to fool.

Every result carries its sample size and a warning when the sample is too small
for the number to mean anything.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.paper import PaperPosition
from app.scoring.config import ScoringConfig, get_scoring_config

# Below this many resolved outcomes, no correlation is reported at all. Chosen
# because a rank correlation on fewer than 20 points is dominated by noise; it
# is not a claim that 20 is enough for confidence, only that fewer is useless.
MIN_SAMPLE = 20
MIN_SAMPLE_FOR_CONFIDENCE = 100


@dataclass
class SignalResult:
    signal: str
    n: int
    coverage: float                    # fraction of positions with this signal present
    spearman: float | None = None
    auc: float | None = None
    mean_sold: float | None = None
    mean_unsold: float | None = None
    lift: float | None = None          # mean_sold / mean_unsold
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SignalPowerReport:
    hypothesis: str
    total_positions: int
    resolved_positions: int
    usable_positions: int
    sold: int
    unsold: int
    sufficient_data: bool
    results: list[SignalResult] = field(default_factory=list)
    ranking: list[str] = field(default_factory=list)
    verdict: str = ""
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = dict(self.__dict__)
        d["results"] = [r.to_dict() for r in self.results]
        return d


def _rank(values: Sequence[float]) -> list[float]:
    """Average ranks, ties shared."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    """Spearman rank correlation. Returns None when either side is constant."""
    if len(xs) < 3 or len(xs) != len(ys):
        return None
    rx, ry = _rank(xs), _rank(ys)
    try:
        return round(statistics.correlation(rx, ry), 4)
    except statistics.StatisticsError:
        return None


def auc_score(values: Sequence[float], labels: Sequence[int]) -> float | None:
    """Area under the ROC curve, via the Mann-Whitney U identity.

    0.5 means the signal is worthless; 1.0 means it ranks every sold domain
    above every unsold one.
    """
    positives = [v for v, y in zip(values, labels) if y == 1]
    negatives = [v for v, y in zip(values, labels) if y == 0]
    if not positives or not negatives:
        return None
    ranks = _rank(list(values))
    pos_rank_sum = sum(r for r, y in zip(ranks, labels) if y == 1)
    n_pos, n_neg = len(positives), len(negatives)
    u = pos_rank_sum - n_pos * (n_pos + 1) / 2.0
    return round(u / (n_pos * n_neg), 4)


def analyse(session: Session, cfg: ScoringConfig | None = None) -> SignalPowerReport:
    cfg = cfg or get_scoring_config()
    experiment = cfg.section("signal_experiment")
    signals: list[str] = list(experiment.get("signals", []))

    positions = session.execute(select(PaperPosition)).scalars().all()
    resolved = [p for p in positions
                if p.outcome in {"SOLD", "UNSOLD", "EXPIRED_UNSOLD"}]

    report = SignalPowerReport(
        hypothesis=str(experiment.get("primary_hypothesis", "")).strip(),
        total_positions=len(positions), resolved_positions=len(resolved),
        usable_positions=len(resolved),
        sold=sum(1 for p in resolved if p.outcome == "SOLD"),
        unsold=sum(1 for p in resolved if p.outcome != "SOLD"),
        sufficient_data=False)

    if len(resolved) < MIN_SAMPLE:
        report.verdict = (
            f"UNDETERMINED. {len(resolved)} resolved outcome(s) against a "
            f"minimum of {MIN_SAMPLE}. No correlation is reported, because a "
            f"rank statistic on this sample would be noise wearing a number's "
            f"clothing. Keep recording paper positions and outcomes.")
        report.warnings.append(
            "This is the expected state of a new installation. The system has "
            "no evidence yet about which signals work.")
        return report

    if report.sold == 0 or report.unsold == 0:
        report.verdict = (
            "UNDETERMINED. Every resolved position has the same outcome, so no "
            "signal can be distinguished from any other.")
        return report

    labels = [1 if p.outcome == "SOLD" else 0 for p in resolved]
    report.sufficient_data = True
    if len(resolved) < MIN_SAMPLE_FOR_CONFIDENCE:
        report.warnings.append(
            f"Sample is {len(resolved)}; below {MIN_SAMPLE_FOR_CONFIDENCE} "
            f"these figures are indicative only and individual signal "
            f"orderings will move around a lot as data arrives.")

    for signal in signals:
        pairs = [(p.signal_snapshot.get(signal), y)
                 for p, y in zip(resolved, labels)]
        usable = [(float(v), y) for v, y in pairs
                  if isinstance(v, (int, float)) and not isinstance(v, bool)]
        coverage = round(len(usable) / len(resolved), 3)
        if len(usable) < MIN_SAMPLE:
            report.results.append(SignalResult(
                signal=signal, n=len(usable), coverage=coverage,
                note=(f"only {len(usable)} position(s) recorded this signal - "
                      f"usually because the provider was not configured at "
                      f"prediction time")))
            continue

        values = [v for v, _ in usable]
        ys = [y for _, y in usable]
        sold_vals = [v for v, y in usable if y == 1]
        unsold_vals = [v for v, y in usable if y == 0]
        mean_sold = statistics.fmean(sold_vals) if sold_vals else None
        mean_unsold = statistics.fmean(unsold_vals) if unsold_vals else None
        lift = (round(mean_sold / mean_unsold, 4)
                if mean_sold is not None and mean_unsold not in (None, 0) else None)

        report.results.append(SignalResult(
            signal=signal, n=len(usable), coverage=coverage,
            spearman=spearman(values, [float(y) for y in ys]),
            auc=auc_score(values, ys),
            mean_sold=round(mean_sold, 4) if mean_sold is not None else None,
            mean_unsold=round(mean_unsold, 4) if mean_unsold is not None else None,
            lift=lift))

    scored = [r for r in report.results if r.auc is not None]
    scored.sort(key=lambda r: abs(r.auc - 0.5), reverse=True)
    report.ranking = [r.signal for r in scored]

    report.verdict = _verdict(scored)
    return report


def _verdict(scored: list[SignalResult]) -> str:
    """Plain-language read of the buyer-depth hypothesis against the traditionals."""
    if not scored:
        return "UNDETERMINED. No signal had enough coverage to evaluate."

    by_name = {r.signal: r for r in scored}
    buyer_signals = [by_name[s] for s in
                     ("buyer_depth_value", "buyer_depth_count", "buyer_quality_max")
                     if s in by_name]
    traditional = [by_name[s] for s in ("search_volume", "cpc") if s in by_name]

    def strength(r: SignalResult) -> float:
        return abs((r.auc or 0.5) - 0.5)

    best = scored[0]
    lines = [f"Strongest signal: {best.signal} (AUC {best.auc}, n={best.n})."]

    if not buyer_signals:
        lines.append("Buyer-depth signals had no coverage - no buyer provider "
                     "was configured when these predictions were made, so the "
                     "primary hypothesis is untested.")
        return " ".join(lines)
    if not traditional:
        lines.append("No keyword signals had coverage, so buyer depth cannot "
                     "yet be compared against the traditional metrics.")
        return " ".join(lines)

    best_buyer = max(buyer_signals, key=strength)
    best_trad = max(traditional, key=strength)
    if strength(best_buyer) > strength(best_trad) * 1.25:
        lines.append(
            f"HYPOTHESIS SUPPORTED so far: {best_buyer.signal} "
            f"(AUC {best_buyer.auc}) outperforms the best traditional metric "
            f"{best_trad.signal} (AUC {best_trad.auc}).")
    elif strength(best_trad) > strength(best_buyer) * 1.25:
        lines.append(
            f"HYPOTHESIS NOT SUPPORTED so far: {best_trad.signal} "
            f"(AUC {best_trad.auc}) outperforms the best buyer-depth signal "
            f"{best_buyer.signal} (AUC {best_buyer.auc}).")
    else:
        lines.append(
            f"INCONCLUSIVE: {best_buyer.signal} (AUC {best_buyer.auc}) and "
            f"{best_trad.signal} (AUC {best_trad.auc}) are too close to "
            f"separate at this sample size.")
    return " ".join(lines)
