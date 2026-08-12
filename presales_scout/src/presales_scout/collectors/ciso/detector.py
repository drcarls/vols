from __future__ import annotations

"""Turn SERP results into a scored CISO signal.

The valuable sales signal is the *negative* one -- "no security leader is
publicly visible" -> a direct CISO-as-a-Service opening. But absence of a
search hit is not proof of absence (private profiles, Swedish-only titles,
tiny firms), so a none_found result always carries verify_recommended=True.
"""

from ...models import CisoSignal, Company, Person
from .base import CisoBackend
from .query import (
    build_query,
    classify_title,
    company_mentioned,
    is_linkedin_profile,
    parse_person,
)


def detect_ciso(company: Company, backend: CisoBackend) -> CisoSignal:
    query = build_query(company.name)
    results = backend.search(query, country=company.country.lower())

    people: list[Person] = []
    for r in results:
        if not is_linkedin_profile(r.link):
            continue
        tier = classify_title(f"{r.title} {r.snippet}")
        if tier is None:
            continue
        matches_company = company_mentioned(company.name, r.title, r.snippet)
        name, role = parse_person(r.title)
        people.append(
            Person(
                name=name or "(unknown)",
                title=role or r.title,
                profile_url=r.link,
                role_tier="leader" if (tier == "leader" and matches_company) else "generic",
            )
        )

    leaders = [p for p in people if p.role_tier == "leader"]

    if leaders:
        # A named leader whose profile ties to this company -> visible, high confidence.
        return CisoSignal(
            status="visible",
            confidence=0.9,
            people=people,
            verify_recommended=False,
            query=query,
            hits_considered=len(results),
        )

    if people:
        # Security people found, but no clear leader tied to the company.
        return CisoSignal(
            status="uncertain",
            confidence=0.55,
            people=people,
            verify_recommended=True,
            query=query,
            hits_considered=len(results),
        )

    # No security-role LinkedIn profiles surfaced -> the sales signal, but soft.
    return CisoSignal(
        status="none_found",
        confidence=0.6,
        people=[],
        verify_recommended=True,
        query=query,
        hits_considered=len(results),
    )
