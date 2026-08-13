from __future__ import annotations

"""External security-hygiene benchmark.

Turns the passive findings for a set of companies into a comparable 0-100
hygiene score, so one firm can be ranked against its peers — the data behind a
"you're bottom-quartile vs your peer group" deliverable.

Deterministic and auditable, by design: the score is 100 minus a
severity-weighted penalty for each observable technical weakness. No model, no
tuning knobs a prospect could dispute — just count the observable gaps, weight
by severity, subtract.

Only *external technical posture* counts, because that's what's comparable
across peers from the outside. Governance/scope/supply signals (no visible
CISO, NIS2 readiness, supplier management) are separate axes and are excluded
here so the benchmark measures one clean thing.
"""

from statistics import quantiles

# not external technical hygiene — scored on their own axes elsewhere
HYGIENE_EXCLUDE = {
    "GOV_NO_CISO", "GOV_NIS2_UNREADY",
    "SUPPLY_UNMANAGED", "SUPPLY_PROCUREMENT_CRITICAL",
    "CRED_BREACH",
}

# penalty by context-adjusted severity_score (1 info … 5 critical)
PENALTY = {1: 3, 2: 6, 3: 10, 4: 16, 5: 24}


def _code(f) -> str:
    return getattr(f, "finding_id", None) or f[0]


def _sev(f) -> int:
    s = getattr(f, "severity_score", None)
    if s is None:
        s = f[1]
    return int(s)


def hygiene_score(findings) -> int:
    """0-100 external-hygiene score for one company from its findings.

    `findings` is any iterable of Finding objects, or (finding_id,
    severity_score) tuples. Excluded (non-hygiene) findings don't count.
    100 = no observable technical gap; clamps at 0.
    """
    penalty = 0
    for f in findings:
        if _code(f) in HYGIENE_EXCLUDE:
            continue
        penalty += PENALTY.get(_sev(f), 0)
    return max(0, 100 - penalty)


def _band(score: float, q1: float | None, q3: float | None) -> str:
    if q1 is None:
        return "mid"
    if score >= q3:
        return "strong"
    if score <= q1:
        return "exposed"
    return "mid"


def rank(company_findings: dict[str, list]) -> list[dict]:
    """Rank companies by hygiene score, best first, with peer-relative context.

    Returns one row per company: rank, name, score, findings (hygiene-relevant
    count), band (strong/mid/exposed by quartile), and percentile (0-100).
    """
    scored = []
    for name, findings in company_findings.items():
        cnt = sum(1 for f in findings if _code(f) not in HYGIENE_EXCLUDE)
        scored.append((name, hygiene_score(findings), cnt))
    scored.sort(key=lambda x: (-x[1], x[0]))

    vals = sorted(s for _, s, _ in scored)
    q1 = q3 = None
    if len(vals) >= 4:
        q1, _, q3 = quantiles(vals, n=4, method="inclusive")

    n = len(scored)
    rows = []
    for i, (name, score, cnt) in enumerate(scored):
        rows.append({
            "rank": i + 1,
            "name": name,
            "score": score,
            "findings": cnt,
            "band": _band(score, q1, q3),
            "percentile": round(100 * (n - i - 1) / (n - 1)) if n > 1 else 100,
        })
    return rows
