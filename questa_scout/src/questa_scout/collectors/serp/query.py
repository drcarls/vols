from __future__ import annotations

"""Query construction and result interpretation for the two SERP signals.

Two narrow questions, one search backend:

1. AI adoption -- is the company actively hiring for AI/GenAI roles? Open
   LLM/ML jobs mean live projects, live data exposure, and budget in motion.
   Query: LinkedIn (and generic) job listings pairing AI-role terms with the
   company name.

2. Governance -- does the company have a *publicly visible* privacy / AI
   governance owner (DPO, Chief Privacy Officer, Head of AI Governance)?
   Query: LinkedIn profiles pairing a governance-leadership title with the
   company name. A hit is the strong (negative-for-us) signal.
"""

import re

# ----- AI-adoption (job posting) signal ------------------------------------

AI_ROLE_TERMS = [
    "Machine Learning Engineer",
    "ML Engineer",
    "AI Engineer",
    "GenAI",
    "Generative AI",
    "LLM",
    "Large Language Model",
    "Prompt Engineer",
    "Data Scientist",
    "AI/ML",
    "Applied Scientist",
    "MLOps",
]

# Strong AI-build roles (as opposed to generic "data scientist") weight higher.
STRONG_AI_TERMS = {
    "genai", "generative ai", "llm", "large language model",
    "prompt engineer", "ai engineer", "mlops",
}


def build_jobs_query(company_name: str) -> str:
    """Google query for open AI/ML job postings at a company."""
    terms = " OR ".join(f'"{t}"' for t in AI_ROLE_TERMS)
    return (
        f'site:linkedin.com/jobs ({terms}) "{company_name}"'
    )


# ----- Governance (privacy / AI-governance leader) signal ------------------

# Governance-LEADERSHIP titles -- a hit here is the strong signal.
LEADER_TITLES = [
    "Data Protection Officer",
    "Chief Privacy Officer",
    "Chief Data Officer",
    "Chief AI Officer",
    "Head of AI Governance",
    "Head of Data Governance",
    "Head of Privacy",
    "VP Privacy",
    "Director of Privacy",
    "Privacy Officer",
    "Responsible AI Lead",
    "AI Governance",
    "Chief Compliance Officer",
]

# Titles that indicate a privacy/governance function but not leadership.
GENERIC_TITLES = [
    "privacy analyst",
    "privacy counsel",
    "data governance analyst",
    "compliance analyst",
    "privacy engineer",
    "data steward",
]

# Broad titles that only weakly imply data/AI governance ownership.
WEAKER_LEADER_TITLES = {"chief compliance officer"}


def build_governance_query(company_name: str) -> str:
    """Google query for LinkedIn privacy/AI-governance leader profiles."""
    titles = " OR ".join(f'"{t}"' for t in LEADER_TITLES)
    return f'site:linkedin.com/in ({titles}) "{company_name}"'


# ----- shared helpers -------------------------------------------------------

def _fold(text: str) -> str:
    return (text or "").lower()


def classify_title(text: str) -> str | None:
    """Return 'leader', 'generic', or None for a governance title/snippet."""
    folded = _fold(text)
    for t in LEADER_TITLES:
        if _fold(t) in folded:
            return "generic" if _fold(t) in {_fold(x) for x in WEAKER_LEADER_TITLES} else "leader"
    for t in GENERIC_TITLES:
        if _fold(t) in folded:
            return "generic"
    return None


def classify_job(text: str) -> str | None:
    """Return 'strong', 'weak', or None for a job-posting title/snippet."""
    folded = _fold(text)
    for t in STRONG_AI_TERMS:
        if t in folded:
            return "strong"
    for t in AI_ROLE_TERMS:
        if _fold(t) in folded:
            return "weak"
    return None


def is_linkedin_profile(link: str) -> bool:
    return "linkedin.com/in/" in (link or "").lower()


def is_job_link(link: str) -> bool:
    low = (link or "").lower()
    return "linkedin.com/jobs" in low or "/job" in low or "careers" in low


def company_mentioned(company_name: str, *texts: str) -> bool:
    needle = _fold(company_name)
    for suffix in (" inc", " inc.", " llc", " llp", " corp", " corporation", " co", " ltd"):
        if needle.endswith(suffix):
            needle = needle[: -len(suffix)]
    needle = needle.strip(" ,.")
    if not needle:
        return False
    hay = _fold(" ".join(t for t in texts if t))
    return needle in hay


_NAME_SPLIT = re.compile(r"\s+[-–—|]\s+")


def parse_person(title: str) -> tuple[str, str]:
    """Split a LinkedIn result title into (name, role text).

    Titles look like: "Jane Doe - Chief Privacy Officer - Acme Inc | LinkedIn".
    """
    cleaned = re.sub(r"\s*\|\s*linkedin\s*$", "", title, flags=re.IGNORECASE).strip()
    parts = _NAME_SPLIT.split(cleaned)
    if not parts:
        return cleaned, ""
    name = parts[0].strip()
    role = " - ".join(p.strip() for p in parts[1:]) if len(parts) > 1 else ""
    return name, role
