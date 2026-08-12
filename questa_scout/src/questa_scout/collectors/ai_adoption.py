from __future__ import annotations

"""AI-adoption signal: is the company actively adopting AI right now?

Two public sources, combined:

  * Job postings -- open AI/ML roles (via the SERP backend). Strong build
    roles (GenAI, LLM, MLOps, AI Engineer) count more than a lone
    "Data Scientist".
  * The company's own homepage -- advertised AI features and a customer-
    facing chatbot (via web_signals).

Active adoption is the buy-now trigger: it means live data flowing to models
and budget already committed -- exactly when Questa's redaction layer is
easiest to sell.
"""

from ..models import AiAdoptionSignal, Company
from .serp.base import SerpBackend
from .serp.query import build_jobs_query, classify_job, company_mentioned
from . import web_signals


def _grade_jobs(company: Company, backend: SerpBackend) -> tuple[bool, bool, int, list[str]]:
    """Return (any_ai_job, strong_ai_job, hits_considered, findings)."""
    query = build_jobs_query(company.name)
    results = backend.search(query, country=(company.country or "us").lower())
    any_job = False
    strong = False
    for r in results:
        tier = classify_job(f"{r.title} {r.snippet}")
        if tier is None:
            continue
        # Require the company name to appear so we don't count a job board's
        # unrelated aggregate page.
        if not company_mentioned(company.name, r.title, r.snippet, r.link):
            continue
        any_job = True
        if tier == "strong":
            strong = True
    findings: list[str] = []
    if strong:
        findings.append("Hiring for GenAI/LLM/MLOps roles")
    elif any_job:
        findings.append("Open AI/ML roles")
    return any_job, strong, len(results), findings


def detect_adoption(
    company: Company,
    backend: SerpBackend,
    *,
    check_web: bool = True,
) -> AiAdoptionSignal:
    any_job, strong_job, hits, findings = _grade_jobs(company, backend)

    public_ai = None
    chatbot = None
    if check_web:
        web = web_signals.fetch_homepage(company.domain)
        if web.reachable:
            public_ai = web.public_ai
            chatbot = web.chatbot
            findings.extend(web.findings or [])

    # Grade. Strong hiring OR a live chatbot -> active. Any weaker single
    # signal -> emerging. Nothing -> none. Nothing checkable -> unknown.
    signals_seen = any_job or (public_ai is not None) or (chatbot is not None)
    if strong_job or chatbot:
        level = "active"
    elif any_job or public_ai:
        level = "emerging"
    elif not signals_seen:
        level = "unknown"
        findings.append("No adoption signal available (no jobs hit, site unreachable)")
    else:
        level = "none"
        findings.append("No public AI-adoption signal found")

    return AiAdoptionSignal(
        level=level,
        hiring=any_job,
        strong_hiring=strong_job,
        public_ai=public_ai,
        chatbot=chatbot,
        hits_considered=hits,
        findings=findings,
    )
