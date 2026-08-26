"""Sensitivity and ablation analysis.

Every weight in this system is a hand-set prior, so the honest question is not
"is the model right?" - it plainly is not yet - but:

    Which conclusions survive being wrong about the priors?

A valuation of $10,781 is a guess. But if `berlinroofing.com` stays in the top
ten across a six-fold swing in the base sell-through rate, then *its position
relative to the other candidates* is carrying information that the dollar
figure is not. That distinction decides whether the system is usable before
calibration: a stable ranking can be acted on today; an unstable one means
nothing here is actionable until outcomes exist.

So this module reports rank stability and level movement **separately**, and
never blends them into a single reassuring number.

Three kinds of analysis:

  * **Parameter sweeps** - vary one prior across a grid, measure how far the
    ranking moves.
  * **Component ablations** - zero each ranking component in turn. Reveals
    which of the nine are actually doing the work, as opposed to which we
    assume are.
  * **Signal ablation** - the buyer-depth hypothesis specifically: how much
    does the ranking change if buyer depth is removed entirely?

Nothing here is persisted. A sweep is analysis of a prediction, not a
prediction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis.rescore import (ScoredRow, StageInputs, load_stage_inputs,
                                  rescore)
from app.analysis.signal_power import spearman
from app.models.analysis import PipelineRun
from app.scoring.config import (ScoringConfig, get_scoring_config,
                                renormalised_weights, with_overrides)

# Sweep grids. Each is centred on the current V0 prior and spans the range a
# reasonable person might argue for, not a range chosen to look stable.
DEFAULT_GRIDS: dict[str, list[float]] = {
    # The single most consequential number in the system. 1-2% is the commonly
    # cited band for retail-priced aftermarket portfolios; the grid spans a
    # 12x range around it because nobody here has measured it.
    "probability.base_annual_sell_through": [0.005, 0.0075, 0.01, 0.015, 0.025,
                                             0.04, 0.06],
    # The hypothesis under test. 0.0 removes buyer depth from the ranking.
    "opportunity.weights.buyer_depth": [0.0, 0.05, 0.10, 0.15, 0.25, 0.35],
    # Recovery on the unsold branch. 0.0 models a pure write-off.
    "economics.unsold_residual_ratio_of_wholesale": [0.0, 0.25, 0.5, 0.75],
    # How much the confidence adjustment can discount a score. 1.0 disables it.
    "opportunity.confidence_floor": [0.3, 0.55, 0.8, 1.0],
}

TOP_K_VALUES = (10, 25, 50, 100)
KENDALL_K = 50

# A ranking is called stable when the baseline top 50 keeps at least this much
# of its membership and this much of its internal order across the sweep.
# Thresholds are judgement calls, stated here rather than buried in prose.
STABLE_OVERLAP = 0.80
STABLE_TAU = 0.70

# A component is called redundant when it varies across the corpus (so it is
# not starved of data) yet removing it barely moves the ranking.
REDUNDANT_INFLUENCE = 0.04
REDUNDANT_SPREAD = 10.0


# --------------------------------------------------------------------------
# rank statistics
# --------------------------------------------------------------------------

def kendall_tau(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    """Kendall's tau-b. O(n^2), so only used on truncated top-K sets.

    Measures how much of the *pairwise order* survives, which is the right
    question for a ranking: swapping ranks 3 and 4 barely matters, swapping
    3 and 300 matters enormously, and tau reflects that where an overlap
    fraction does not.
    """
    n = len(xs)
    if n < 2 or n != len(ys):
        return None
    concordant = discordant = tied_x = tied_y = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = xs[i] - xs[j]
            dy = ys[i] - ys[j]
            if dx == 0 and dy == 0:
                tied_x += 1
                tied_y += 1
                continue
            if dx == 0:
                tied_x += 1
                continue
            if dy == 0:
                tied_y += 1
                continue
            if (dx > 0) == (dy > 0):
                concordant += 1
            else:
                discordant += 1
    total = n * (n - 1) / 2
    denominator = ((total - tied_x) * (total - tied_y)) ** 0.5
    if denominator == 0:
        return None
    return round((concordant - discordant) / denominator, 4)


def _ranks(rows: Sequence[ScoredRow]) -> dict[int, int]:
    return {row.domain_id: position for position, row in enumerate(rows, start=1)}


def _median(values: Sequence[float]) -> float | None:
    import statistics
    clean = [v for v in values if v is not None]
    return round(float(statistics.median(clean)), 2) if clean else None


@dataclass
class RankStability:
    """How much the ordering moved, measured several ways."""

    top_k_overlap: dict[int, float] = field(default_factory=dict)
    kendall_tau_top: float | None = None
    spearman_full: float | None = None
    median_rank_shift: float | None = None
    max_rank_shift: int | None = None
    entered_top25: list[str] = field(default_factory=list)
    left_top25: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = dict(self.__dict__)
        d["top_k_overlap"] = {str(k): v for k, v in self.top_k_overlap.items()}
        return d


def compare_rankings(baseline: Sequence[ScoredRow],
                     variant: Sequence[ScoredRow]) -> RankStability:
    base_ranks, var_ranks = _ranks(baseline), _ranks(variant)
    stability = RankStability()

    for k in TOP_K_VALUES:
        if k > len(baseline):
            continue
        base_top = {r.domain_id for r in baseline[:k]}
        var_top = {r.domain_id for r in variant[:k]}
        stability.top_k_overlap[k] = round(len(base_top & var_top) / k, 4)

    k = min(KENDALL_K, len(baseline))
    if k >= 2:
        subset = [r.domain_id for r in baseline[:k]]
        stability.kendall_tau_top = kendall_tau(
            [base_ranks[d] for d in subset], [var_ranks[d] for d in subset])
        shifts = [abs(var_ranks[d] - base_ranks[d]) for d in subset]
        stability.median_rank_shift = _median(shifts)
        stability.max_rank_shift = max(shifts)

    common = [d for d in base_ranks if d in var_ranks]
    if len(common) >= 3:
        stability.spearman_full = spearman(
            [float(base_ranks[d]) for d in common],
            [float(var_ranks[d]) for d in common])

    if len(baseline) >= 25:
        by_id = {r.domain_id: r.domain for r in list(baseline) + list(variant)}
        base_25 = {r.domain_id for r in baseline[:25]}
        var_25 = {r.domain_id for r in variant[:25]}
        stability.entered_top25 = sorted(by_id[d] for d in var_25 - base_25)
        stability.left_top25 = sorted(by_id[d] for d in base_25 - var_25)
    return stability


def summarise_levels(rows: Sequence[ScoredRow]) -> dict[str, Any]:
    """Level summary. Deliberately separate from rank stability."""
    recommendations: dict[str, int] = {}
    for row in rows:
        recommendations[row.recommendation] = recommendations.get(
            row.recommendation, 0) + 1
    return {
        "median_score": _median([r.score for r in rows]),
        "median_retail_value_mid": _median([r.retail_value_mid for r in rows]),
        "median_prob_sale_24m": _median([r.prob_sale_24m for r in rows]),
        "median_expected_profit_24m": _median(
            [r.expected_profit_24m for r in rows
             if r.expected_profit_24m is not None]),
        "median_recommended_max_bid": _median(
            [r.recommended_max_bid for r in rows
             if r.recommended_max_bid is not None]),
        "positive_expected_profit": sum(
            1 for r in rows
            if r.expected_profit_24m is not None and r.expected_profit_24m > 0),
        "recommendations": dict(sorted(recommendations.items())),
    }


# --------------------------------------------------------------------------
# sweeps and ablations
# --------------------------------------------------------------------------

@dataclass
class SweepPoint:
    label: str
    value: Any
    is_baseline: bool
    stability: RankStability
    levels: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"label": self.label, "value": self.value,
                "is_baseline": self.is_baseline,
                "stability": self.stability.to_dict(), "levels": self.levels}


@dataclass
class Sweep:
    parameter: str
    baseline_value: Any
    points: list[SweepPoint] = field(default_factory=list)
    min_top50_overlap: float | None = None
    min_kendall_tau: float | None = None
    # Ratio of max to min median recommended max bid across the grid. The bid is
    # used rather than expected profit because profit medians go negative on a
    # realistic corpus, and a ratio of two negative numbers is meaningless.
    level_swing: float | None = None
    profit_shift: float | None = None     # absolute move in median expected profit
    stable: bool = False
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = dict(self.__dict__)
        d["points"] = [p.to_dict() for p in self.points]
        return d


def _variant_for(cfg: ScoringConfig, parameter: str, value: Any) -> ScoringConfig:
    """Build the config variant for one sweep point.

    Opportunity weights are special-cased: setting one weight requires
    rescaling the rest, or the score would no longer be on a 0-100 scale and
    the recommendation thresholds would stop meaning anything.
    """
    label = f"{parameter}={value}"
    if parameter.startswith("opportunity.weights."):
        component = parameter.rsplit(".", 1)[1]
        return with_overrides(
            cfg, {"opportunity.weights": renormalised_weights(cfg, component, value)},
            label=label)
    return with_overrides(cfg, {parameter: value}, label=label)


def run_sweep(cfg: ScoringConfig, inputs: Sequence[StageInputs], parameter: str,
              grid: Sequence[Any], baseline_rows: Sequence[ScoredRow]) -> Sweep:
    if parameter.startswith("opportunity.weights."):
        baseline_value = cfg.get(parameter)
    else:
        baseline_value = cfg.get(parameter)

    sweep = Sweep(parameter=parameter, baseline_value=baseline_value)
    overlaps: list[float] = []
    taus: list[float] = []
    profits: list[float] = []
    bids: list[float] = []

    for value in grid:
        variant_cfg = _variant_for(cfg, parameter, value)
        rows = rescore(variant_cfg, inputs)
        stability = compare_rankings(baseline_rows, rows)
        levels = summarise_levels(rows)
        is_baseline = (baseline_value is not None
                       and abs(float(value) - float(baseline_value)) < 1e-12)
        sweep.points.append(SweepPoint(
            label=f"{value}", value=value, is_baseline=is_baseline,
            stability=stability, levels=levels))

        if not is_baseline:
            if 50 in stability.top_k_overlap:
                overlaps.append(stability.top_k_overlap[50])
            elif stability.top_k_overlap:
                overlaps.append(min(stability.top_k_overlap.values()))
            if stability.kendall_tau_top is not None:
                taus.append(stability.kendall_tau_top)
        profit = levels.get("median_expected_profit_24m")
        if profit is not None:
            profits.append(profit)
        bid = levels.get("median_recommended_max_bid")
        if bid is not None:
            bids.append(bid)

    sweep.min_top50_overlap = round(min(overlaps), 4) if overlaps else None
    sweep.min_kendall_tau = round(min(taus), 4) if taus else None
    if len(bids) >= 2 and min(bids) > 0:
        sweep.level_swing = round(max(bids) / min(bids), 2)
    if len(profits) >= 2:
        sweep.profit_shift = round(max(profits) - min(profits), 2)

    sweep.stable = bool(
        sweep.min_top50_overlap is not None
        and sweep.min_top50_overlap >= STABLE_OVERLAP
        and (sweep.min_kendall_tau is None or sweep.min_kendall_tau >= STABLE_TAU))

    is_weight = parameter.startswith("opportunity.weights.")
    if sweep.min_top50_overlap is None:
        sweep.note = (f"Sensitivity to {parameter} could not be measured on "
                      f"this corpus (too few domains).")
    elif is_weight:
        # Framing matters here. A weight sweep moving the ranking is not a
        # defect - moving the ranking is what a weight is for. The useful
        # reading is how much of the ordering this one judgement call decides.
        sweep.note = (
            f"This weight decides up to {1 - sweep.min_top50_overlap:.0%} of "
            f"the top 50 across the grid. That is the share of the ranking "
            f"resting on one hand-set judgement, not evidence of instability.")
    elif sweep.stable:
        sweep.note = (
            f"Ranking is robust to {parameter}: across the whole grid the "
            f"baseline top 50 keeps at least "
            f"{sweep.min_top50_overlap:.0%} of its membership"
            + (f" and tau stays at or above {sweep.min_kendall_tau}."
               if sweep.min_kendall_tau is not None else "."))
    else:
        sweep.note = (
            f"Ranking is SENSITIVE to {parameter}: top-50 membership falls to "
            f"{sweep.min_top50_overlap:.0%} somewhere in the grid.")
    return sweep


@dataclass
class Ablation:
    component: str
    weight: float
    stability: RankStability
    levels: dict[str, Any]
    influence: float | None = None   # 1 - top50 overlap; higher = more load-bearing
    coverage: float = 0.0            # fraction of domains where the component had data
    spread: float = 0.0              # std-dev of the component value across domains
    diagnosis: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"component": self.component, "weight": self.weight,
                "influence": self.influence, "coverage": self.coverage,
                "spread": self.spread, "diagnosis": self.diagnosis,
                "stability": self.stability.to_dict(), "levels": self.levels}


def run_ablations(cfg: ScoringConfig, inputs: Sequence[StageInputs],
                  baseline_rows: Sequence[ScoredRow]) -> list[Ablation]:
    """Zero each ranking component in turn and see how far the ranking moves.

    The weight is removed and the remaining eight are rescaled to sum to 1, so
    the score stays on a 0-100 scale and the recommendation thresholds keep
    their meaning. Without that rescale every ablation would look identical:
    a uniform shrink of the raw score leaves the ordering untouched.

    ``influence`` is 1 minus the top-50 overlap. A component whose removal
    changes nothing is decoration, whatever weight the config gives it.
    """
    # Coverage and spread of each component across the baseline cohort. A
    # component that is MISSING everywhere, or constant everywhere, cannot
    # discriminate - and that is a statement about the DATA, not about whether
    # the component is worth having. Conflating the two would quietly argue for
    # deleting exactly the signals we have not sourced yet.
    coverage: dict[str, float] = {}
    spread: dict[str, float] = {}
    if baseline_rows:
        import statistics
        names = list(cfg.get("opportunity.weights"))
        for name in names:
            entries = [r.components.get(name, {}) for r in baseline_rows]
            present = [e for e in entries if e.get("status") == "OK"]
            coverage[name] = round(len(present) / len(entries), 4)
            values = [float(e.get("value", 0.0)) for e in entries]
            spread[name] = (round(statistics.pstdev(values), 4)
                            if len(values) > 1 else 0.0)

    results: list[Ablation] = []
    for component, weight in cfg.get("opportunity.weights").items():
        variant = with_overrides(
            cfg, {"opportunity.weights": renormalised_weights(cfg, component, 0.0)},
            label=f"ablate:{component}")
        rows = rescore(variant, inputs)
        stability = compare_rankings(baseline_rows, rows)
        overlap = stability.top_k_overlap.get(
            50, min(stability.top_k_overlap.values(), default=None))
        influence = round(1.0 - overlap, 4) if overlap is not None else None
        cov, spr = coverage.get(component, 0.0), spread.get(component, 0.0)

        if influence is None:
            diagnosis = "not measurable on this corpus"
        elif influence >= 0.10:
            diagnosis = "load-bearing"
        elif cov < 0.05:
            diagnosis = ("NO DATA - the component was MISSING for "
                         f"{1 - cov:.0%} of domains, so it is constant and "
                         f"cannot discriminate. This says nothing about its "
                         f"value once the data source is configured.")
        elif spr < 1.0:
            diagnosis = (f"near-constant across this corpus (spread {spr:.2f} "
                         f"points), so it separates nothing here")
        elif influence <= REDUNDANT_INFLUENCE and spr >= REDUNDANT_SPREAD:
            diagnosis = (f"REDUNDANT - varies widely across domains "
                         f"(spread {spr:.1f} points) yet removing it changes "
                         f"only {influence:.0%} of the top 50, so another "
                         f"component already carries its information")
        else:
            diagnosis = "minor contributor"

        results.append(Ablation(
            component=component, weight=float(weight), stability=stability,
            levels=summarise_levels(rows), influence=influence,
            coverage=cov, spread=spr, diagnosis=diagnosis))
    results.sort(key=lambda a: (a.influence if a.influence is not None else -1),
                 reverse=True)
    return results


@dataclass
class WeightGap:
    """Configured weight versus the weight the ranking actually behaves as if
    it had.

    A weight is an *intention*. Influence is what the corpus does with it. When
    the two disagree the config is describing a model that is not the model
    being run, and the disagreement is usually diagnostic: a component with a
    big weight and no influence is either missing its data or duplicating
    another component.
    """

    component: str
    configured_weight: float
    configured_share: float
    influence: float | None
    effective_share: float | None
    gap: float | None           # effective share minus configured share
    diagnosis: str

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SensitivityReport:
    run_id: int
    baseline_config: str
    calibrated: bool
    domains: int
    sweeps: list[Sweep] = field(default_factory=list)
    ablations: list[Ablation] = field(default_factory=list)
    weight_gaps: list[WeightGap] = field(default_factory=list)
    verdict: str = ""
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = dict(self.__dict__)
        d["sweeps"] = [s.to_dict() for s in self.sweeps]
        d["ablations"] = [a.to_dict() for a in self.ablations]
        d["weight_gaps"] = [w.to_dict() for w in self.weight_gaps]
        return d


def compute_weight_gaps(cfg: ScoringConfig,
                        ablations: Sequence[Ablation]) -> list[WeightGap]:
    """Compare each component's configured share of the weight against its
    share of the measured influence."""
    total_influence = sum(a.influence for a in ablations
                          if a.influence is not None)
    gaps: list[WeightGap] = []
    for ablation in ablations:
        configured_share = ablation.weight    # weights already sum to 1.0
        effective_share = (round(ablation.influence / total_influence, 4)
                           if ablation.influence is not None and total_influence > 0
                           else None)
        gaps.append(WeightGap(
            component=ablation.component,
            configured_weight=ablation.weight,
            configured_share=round(configured_share, 4),
            influence=ablation.influence,
            effective_share=effective_share,
            gap=(round(effective_share - configured_share, 4)
                 if effective_share is not None else None),
            diagnosis=ablation.diagnosis))
    gaps.sort(key=lambda g: (g.gap if g.gap is not None else 0.0))
    return gaps


MIN_DOMAINS_FOR_STABILITY = 100


def analyse(session: Session, *, run_id: int | None = None,
            cfg: ScoringConfig | None = None,
            grids: dict[str, list[float]] | None = None,
            include_ablations: bool = True) -> SensitivityReport:
    """Full sensitivity analysis of one completed run."""
    cfg = cfg or get_scoring_config()
    if run_id is None:
        run_id = session.execute(
            select(PipelineRun.id).where(PipelineRun.status == "complete")
            .order_by(PipelineRun.id.desc()).limit(1)).scalar()
    if run_id is None:
        return SensitivityReport(
            run_id=-1, baseline_config=cfg.stamp, calibrated=cfg.calibrated,
            domains=0, verdict="No completed pipeline run to analyse.",
            warnings=["Run the pipeline first."])

    inputs = load_stage_inputs(session, run_id)
    report = SensitivityReport(run_id=run_id, baseline_config=cfg.stamp,
                               calibrated=cfg.calibrated, domains=len(inputs))
    if not inputs:
        report.verdict = "That run scored no domains."
        return report

    if len(inputs) < MIN_DOMAINS_FOR_STABILITY:
        report.warnings.append(
            f"Only {len(inputs)} domains in this run. Rank-stability figures on "
            f"a corpus this small are indicative at best; a single domain "
            f"moving swings every overlap fraction by several percent. Run this "
            f"against at least {MIN_DOMAINS_FOR_STABILITY} domains before "
            f"drawing conclusions.")

    report.warnings.append(
        "Component influence is a property of THIS corpus, not of the model. A "
        "component only discriminates where the domains actually differ on it: "
        "a corpus of near-identical names will make almost everything look "
        "redundant. Re-run this against the inventory you actually screen "
        "before acting on any influence figure.")

    baseline_rows = rescore(cfg, inputs)
    for parameter, grid in (grids or DEFAULT_GRIDS).items():
        report.sweeps.append(run_sweep(cfg, inputs, parameter, grid, baseline_rows))
    if include_ablations:
        report.ablations = run_ablations(cfg, inputs, baseline_rows)
        report.weight_gaps = compute_weight_gaps(cfg, report.ablations)

    report.verdict = _verdict(report)
    return report


def _verdict(report: SensitivityReport) -> str:
    """Plain-language read: is the ranking usable before calibration?"""
    if not report.sweeps:
        return "No sweeps were run."

    base_rate = next((s for s in report.sweeps
                      if s.parameter == "probability.base_annual_sell_through"), None)
    lines: list[str] = []

    if base_rate is not None and base_rate.min_top50_overlap is not None:
        swing = ""
        if base_rate.level_swing:
            swing = (f" Over the same grid the median recommended maximum bid "
                     f"moves {base_rate.level_swing:.1f}x")
            if base_rate.profit_shift:
                swing += (f" and the median expected profit shifts by "
                          f"${base_rate.profit_shift:,.0f}")
            swing += "."
        if base_rate.stable:
            lines.append(
                f"RANKING IS ROBUST to the base sell-through rate: across a "
                f"12x swing the baseline top 50 keeps "
                f"{base_rate.min_top50_overlap:.0%} of its membership "
                f"(tau >= {base_rate.min_kendall_tau}).{swing} The *relative* "
                f"ordering carries information the dollar figures do not, so it "
                f"is reasonable to paper-buy off the ranking now while treating "
                f"every currency amount as unverified.")
        else:
            lines.append(
                f"RANKING IS SENSITIVE to the base sell-through rate: top-50 "
                f"membership falls to {base_rate.min_top50_overlap:.0%} within "
                f"the grid.{swing} Neither the ordering nor the levels can be "
                f"acted on until the base rate is measured against outcomes.")

    unstable = [s.parameter for s in report.sweeps
                if not s.stable and s.min_top50_overlap is not None
                and s.parameter != "probability.base_annual_sell_through"
                and not s.parameter.startswith("opportunity.weights.")]
    if unstable:
        lines.append(f"Also sensitive to these priors: {', '.join(unstable)}.")

    weight_sweeps = [s for s in report.sweeps
                     if s.parameter.startswith("opportunity.weights.")
                     and s.min_top50_overlap is not None]
    for sweep in weight_sweeps:
        component = sweep.parameter.rsplit(".", 1)[1]
        lines.append(
            f"The {component} weight decides up to "
            f"{1 - sweep.min_top50_overlap:.0%} of the top 50 across its grid - "
            f"more than the base rate does, so which names surface depends more "
            f"on that one judgement call than on the sell-through prior.")

    if report.ablations:
        load_bearing = [a for a in report.ablations
                        if a.influence is not None and a.influence >= 0.10]
        starved = [a for a in report.ablations if a.diagnosis.startswith("NO DATA")]
        redundant = [a for a in report.ablations
                     if a.diagnosis.startswith("redundant")]
        if load_bearing:
            lines.append(
                "Load-bearing components (removing them moves the top 50 by "
                "10% or more): "
                + ", ".join(f"{a.component} ({a.influence:.0%})"
                            for a in load_bearing) + ".")
        if starved:
            starved_weight = sum(a.weight for a in starved)
            lines.append(
                f"{starved_weight:.0%} of the configured weight sits on "
                f"components with NO DATA on this corpus ("
                + ", ".join(a.component for a in starved)
                + "), so they are constant and discriminate nothing. That is a "
                  "missing data source, not a bad weight - configure the "
                  "provider and re-run this analysis before changing the config.")
        if redundant:
            lines.append(
                "Redundant components (data present, but another component "
                "already carries the same information): "
                + ", ".join(f"{a.component} (weight {a.weight:.2f}, influence "
                            f"{a.influence:.0%})" for a in redundant) + ".")

    if report.weight_gaps:
        worst = report.weight_gaps[0]
        if worst.gap is not None and worst.gap <= -0.10:
            lines.append(
                f"Largest weight/influence gap: {worst.component} is given "
                f"{worst.configured_share:.0%} of the configured weight but "
                f"accounts for {worst.effective_share:.0%} of the measured "
                f"influence. The config is describing a model that is not the "
                f"model being run.")

    buyer = next((a for a in report.ablations if a.component == "buyer_depth"), None)
    if buyer is not None and buyer.influence is not None:
        lines.append(
            f"Buyer depth specifically: removing it changes "
            f"{buyer.influence:.0%} of the top 50. That is how much of the "
            f"current ranking rests on the hypothesis under test - it does not "
            f"say whether the hypothesis is correct, only how much would change "
            f"if it were abandoned.")
    return " ".join(lines)


def render_text(report: SensitivityReport) -> str:
    """Terminal rendering of a sensitivity report."""
    out: list[str] = []
    out.append("=" * 78)
    out.append("SENSITIVITY AND ABLATION ANALYSIS")
    out.append(f"run {report.run_id}  |  {report.domains} domains  |  "
               f"baseline config {report.baseline_config}")
    out.append("=" * 78)
    for warning in report.warnings:
        out.append(f"  ! {warning}")
    out.append("")
    out.append("VERDICT")
    for chunk in report.verdict.split(". "):
        if chunk.strip():
            out.append(f"  {chunk.strip().rstrip('.')}.")
    out.append("")

    for sweep in report.sweeps:
        out.append("-" * 78)
        flag = "STABLE" if sweep.stable else "SENSITIVE"
        out.append(f"SWEEP  {sweep.parameter}   [{flag}]")
        out.append(f"       baseline = {sweep.baseline_value}")
        out.append(f"  {'value':>10s} {'top10':>7s} {'top25':>7s} {'top50':>7s} "
                   f"{'tau50':>7s} {'medshift':>9s} {'med profit':>11s} "
                   f"{'med bid':>9s}  recommendations")
        for point in sweep.points:
            marker = " *" if point.is_baseline else "  "
            overlap = point.stability.top_k_overlap
            profit = point.levels.get("median_expected_profit_24m")
            bid = point.levels.get("median_recommended_max_bid")
            out.append(
                f"{marker}{point.label:>9s} "
                f"{_pct(overlap.get(10)):>7s} {_pct(overlap.get(25)):>7s} "
                f"{_pct(overlap.get(50)):>7s} "
                f"{_num(point.stability.kendall_tau_top):>7s} "
                f"{_num(point.stability.median_rank_shift):>9s} "
                f"{_money(profit):>11s} {_money(bid):>9s}  "
                f"{_recs(point.levels.get('recommendations', {}))}")
        out.append(f"  {sweep.note}")
        if sweep.level_swing:
            line = (f"  Median recommended max bid moves "
                    f"{sweep.level_swing:.1f}x across this grid")
            if sweep.profit_shift:
                line += (f"; median expected profit shifts by "
                         f"${sweep.profit_shift:,.0f}")
            out.append(line + ".")
        out.append("")

    if report.ablations:
        out.append("-" * 78)
        out.append("COMPONENT ABLATION  (zero one weight, rescale the rest)")
        out.append(f"  {'component':<24s} {'weight':>7s} {'influence':>10s} "
                   f"{'cover':>7s} {'spread':>7s} {'top50':>7s} {'tau50':>7s}")
        for ablation in report.ablations:
            overlap = ablation.stability.top_k_overlap
            out.append(
                f"  {ablation.component:<24s} {ablation.weight:>7.2f} "
                f"{_pct(ablation.influence):>10s} {_pct(ablation.coverage):>7s} "
                f"{ablation.spread:>7.1f} {_pct(overlap.get(50)):>7s} "
                f"{_num(ablation.stability.kendall_tau_top):>7s}")
        out.append("")
        out.append("  'influence' is the fraction of the top 50 that changes when the")
        out.append("  component is removed. 'cover' is the fraction of domains where the")
        out.append("  component had data at all - low influence with low cover means a")
        out.append("  missing data source, not a useless component.")
        out.append("")

    if report.weight_gaps:
        out.append("-" * 78)
        out.append("CONFIGURED WEIGHT vs MEASURED INFLUENCE")
        out.append(f"  {'component':<24s} {'config':>7s} {'effective':>10s} "
                   f"{'gap':>7s} {'cover':>7s}  diagnosis")
        by_component = {a.component: a for a in report.ablations}
        for gap in report.weight_gaps:
            ablation = by_component.get(gap.component)
            out.append(
                f"  {gap.component:<24s} {gap.configured_share:>7.0%} "
                f"{_pct(gap.effective_share):>10s} "
                f"{(f'{gap.gap:+.0%}' if gap.gap is not None else '-'):>7s} "
                f"{_pct(ablation.coverage if ablation else None):>7s}  "
                f"{gap.diagnosis}")
        out.append("")
        out.append("  'effective' is the component's share of total measured influence.")
        out.append("  A large negative gap means the config claims the component matters")
        out.append("  more than the corpus says it does.")
    out.append("-" * 78)
    return "\n".join(out)


def _pct(value: float | None) -> str:
    return "-" if value is None else f"{value:.0%}"


def _num(value: float | None) -> str:
    return "-" if value is None else f"{value:.2f}"


def _money(value: float | None) -> str:
    return "-" if value is None else f"${value:,.0f}"


def _recs(counts: dict[str, int]) -> str:
    order = ["STRONG_BUY", "BUY", "WATCH", "PASS", "AVOID"]
    return " ".join(f"{name[:1] if name != 'STRONG_BUY' else 'SB'}:{counts[name]}"
                    for name in order if counts.get(name))
