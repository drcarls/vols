from __future__ import annotations

"""Query construction and result interpretation for CISO detection.

The signal we want is narrow: does this company have a *publicly visible*
security leader? We ask a search engine for LinkedIn profiles that pair a
security-leadership title with the company name -- in both English and
Swedish, since Swedish titles (sakerhetschef, informationssakerhetschef)
carry most of the recall for the target market.
"""

import re

# Security-LEADERSHIP titles -- a hit here is the strong signal.
LEADER_TITLES = [
    "CISO",
    "Chief Information Security Officer",
    "Chief Security Officer",
    "Head of Information Security",
    "Head of Security",
    "Head of Cyber Security",
    "Head of IT Security",
    "VP Security",
    "Director of Security",
    "Security Director",
    # Swedish
    "informationssakerhetschef",
    "IT-sakerhetschef",
    "cybersakerhetschef",
    "sakerhetschef",  # broader (can be physical security) -> treated as weaker
]

# Titles that indicate a security function but not leadership.
GENERIC_TITLES = [
    "security engineer",
    "security analyst",
    "security consultant",
    "sakerhetsanalytiker",
    "security specialist",
]

# The Swedish "sakerhetschef" alone can mean physical/facility security, so
# it is scored a tier below the infosec-specific titles.
WEAKER_LEADER_TITLES = {"sakerhetschef"}


def build_query(company_name: str) -> str:
    """Build a Google query for LinkedIn security-leader profiles at a company."""
    titles = " OR ".join(f'"{t}"' for t in LEADER_TITLES)
    return f'site:linkedin.com/in ({titles}) "{company_name}"'


def _fold(text: str) -> str:
    """Lowercase and strip Swedish diacritics for tolerant matching."""
    text = text.lower()
    for a, b in (("å", "a"), ("ä", "a"), ("ö", "o")):
        text = text.replace(a, b)
    return text


def classify_title(text: str) -> str | None:
    """Return 'leader', 'generic', or None for a title/snippet string."""
    folded = _fold(text)
    for t in LEADER_TITLES:
        if _fold(t) in folded:
            return "generic" if _fold(t) in {_fold(x) for x in WEAKER_LEADER_TITLES} else "leader"
    for t in GENERIC_TITLES:
        if _fold(t) in folded:
            return "generic"
    return None


def is_linkedin_profile(link: str) -> bool:
    return "linkedin.com/in/" in (link or "").lower()


def company_mentioned(company_name: str, *texts: str) -> bool:
    needle = _fold(company_name)
    # Drop common legal suffixes from the needle for looser matching.
    for suffix in (" ab (publ)", " ab", " hb", " kb"):
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

    LinkedIn titles look like: "Anna Svensson - CISO - Acme AB | LinkedIn".
    We take the first segment as the name and the rest as the role/company.
    """
    cleaned = re.sub(r"\s*\|\s*linkedin\s*$", "", title, flags=re.IGNORECASE).strip()
    parts = _NAME_SPLIT.split(cleaned)
    if not parts:
        return cleaned, ""
    name = parts[0].strip()
    role = " - ".join(p.strip() for p in parts[1:]) if len(parts) > 1 else ""
    return name, role
