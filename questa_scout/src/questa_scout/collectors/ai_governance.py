from __future__ import annotations

"""Turn SERP results into a scored governance signal.

The valuable sales signal is the *negative* one -- "no privacy / AI
governance owner is publicly visible" while the company is adopting AI ->
a direct Questa opening. But absence of a search hit is not proof of absence
(private profiles, outsourced DPOs, small firms), so a none_found result
always carries verify_recommended=True.
"""

from ..models import Company, GovernanceSignal, Person
from .serp.base import SerpBackend
from .serp.query import (
    build_governance_query,
    classify_title,
    company_mentioned,
    is_linkedin_profile,
    parse_person,
)


def detect_governance(company: Company, backend: SerpBackend) -> GovernanceSignal:
    query = build_governance_query(company.name)
    results = backend.search(query, country=(company.country or "us").lower())

    people: list[Person] = []
    for r in results:
        if not is_linkedin_profile(r.link):
            continue
        tier = classify_title(f"{r.title} {r.snippet}")
        if tier is None:
            continue
        # A company-specific signal must ignore profiles that aren't about
        # this company. Search engines happily return generic "Chief Privacy
        # Officer" profiles (at other employers) for any company query; those
        # are noise, not evidence of *this* company's governance. Only keep
        # results that actually mention the company.
        if not company_mentioned(company.name, r.title, r.snippet):
            continue
        name, role = parse_person(r.title)
        people.append(
            Person(
                name=name or "(unknown)",
                title=role or r.title,
                profile_url=r.link,
                role_tier="leader" if tier == "leader" else "generic",
            )
        )

    leaders = [p for p in people if p.role_tier == "leader"]

    if leaders:
        # A named governance leader tied to this company -> governed.
        return GovernanceSignal(
            status="governed",
            confidence=0.9,
            people=people,
            verify_recommended=False,
            query=query,
            hits_considered=len(results),
        )

    if people:
        # Privacy/compliance staff found, but no clear owner tied to the company.
        return GovernanceSignal(
            status="uncertain",
            confidence=0.55,
            people=people,
            verify_recommended=True,
            query=query,
            hits_considered=len(results),
        )

    # No governance-role profiles surfaced -> the sales signal, but soft.
    return GovernanceSignal(
        status="none_found",
        confidence=0.6,
        people=[],
        verify_recommended=True,
        query=query,
        hits_considered=len(results),
    )
