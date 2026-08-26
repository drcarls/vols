"""Semantic classification: what is this domain *about*?

Two passes, always in this order:

  1. A deterministic pass over the taxonomy. Fast, free, auditable, and it
     records exactly which token produced the classification.
  2. An optional LLM pass, used only when the deterministic pass is
     low-confidence, and only to fill in category / intent / audience. Its
     output is marked LLM_INFERRED and never overwrites a confident
     deterministic result.

If no LLM is configured, pass 2 is skipped and the affected fields stay as the
deterministic result or MISSING. Nothing is fabricated to fill the gap.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.providers.llm import LlmProvider, LlmUnavailable
from app.provenance import Sourced, derived, llm_inferred, missing
from app.scoring.taxonomy import (INFORMATIONAL_TOKENS, KEYWORD_TO_CATEGORY,
                                  TRANSACTIONAL_TOKENS, geo_scope)

CLASSIFY_SCHEMA = json.dumps({
    "type": "object",
    "properties": {
        "category": {"type": "string",
                     "description": "single lowercase industry slug"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "intent_type": {"type": "string",
                        "enum": ["transactional", "commercial",
                                 "informational", "navigational"]},
        "audience": {"type": "string", "enum": ["b2b", "b2c", "both", "unclear"]},
        "reasoning": {"type": "string"},
    },
    "required": ["category", "confidence", "intent_type", "audience", "reasoning"],
})


@dataclass
class Classification:
    category: Sourced[str]
    intent_type: Sourced[str]
    audience: Sourced[str]
    geo_specificity: Sourced[str]
    geo_token: str | None
    matched_tokens: list[str]
    reasoning: str | None = None

    def as_records(self) -> dict[str, Sourced[Any]]:
        return {"category": self.category, "intent_type": self.intent_type,
                "audience": self.audience, "geo_specificity": self.geo_specificity}


def classify_deterministic(words: list[str]) -> Classification:
    """Taxonomy lookup. Every result names the token that produced it."""
    matched: list[tuple[str, str]] = []
    for w in words:
        cat = KEYWORD_TO_CATEGORY.get(w)
        if cat:
            matched.append((w, cat))

    if matched:
        # Prefer the most specific signal: the last matched token in a name is
        # usually the head noun ("berlin roofing" -> construction).
        token, category = matched[-1]
        # Confidence rises when several tokens agree.
        cats = {c for _, c in matched}
        conf = 0.85 if len(cats) == 1 else 0.6
        cat_sourced = derived(category, "taxonomy.deterministic", confidence=conf,
                              note=f"matched token(s): "
                                   f"{', '.join(t for t, _ in matched)}")
    else:
        cat_sourced = missing("taxonomy.deterministic",
                              "no taxonomy token matched; category unknown")

    word_set = set(words)
    if word_set & TRANSACTIONAL_TOKENS:
        hits = sorted(word_set & TRANSACTIONAL_TOKENS)
        intent = derived("transactional", "taxonomy.deterministic", confidence=0.7,
                         note=f"transactional token(s): {', '.join(hits)}")
    elif word_set & INFORMATIONAL_TOKENS:
        hits = sorted(word_set & INFORMATIONAL_TOKENS)
        intent = derived("informational", "taxonomy.deterministic", confidence=0.7,
                         note=f"informational token(s): {', '.join(hits)}")
    elif not cat_sourced.is_missing:
        # A recognised industry noun with no verb reads as commercial browsing
        # intent rather than a transaction.
        intent = derived("commercial", "taxonomy.deterministic", confidence=0.45,
                         note="industry noun with no explicit action token")
    else:
        intent = missing("taxonomy.deterministic", "no intent tokens matched")

    scope, geo_token = geo_scope(words)
    geo = derived(scope, "taxonomy.deterministic", confidence=0.8,
                  note=(f"matched place name: {geo_token}" if geo_token
                        else "no place name found"))

    return Classification(category=cat_sourced, intent_type=intent,
                          audience=missing("taxonomy.deterministic",
                                           "audience is not deterministically inferable"),
                          geo_specificity=geo, geo_token=geo_token,
                          matched_tokens=[t for t, _ in matched])


LLM_CONFIDENCE_THRESHOLD = 0.7


def classify(domain: str, words: list[str], llm: LlmProvider | None = None,
             *, allow_llm: bool = True) -> Classification:
    """Deterministic classification, optionally refined by an LLM.

    The LLM is consulted only when the deterministic pass is unsure. That keeps
    cost proportional to genuine ambiguity rather than to corpus size.
    """
    result = classify_deterministic(words)

    needs_help = (result.category.is_missing
                  or result.category.confidence < LLM_CONFIDENCE_THRESHOLD
                  or result.audience.is_missing)
    if not (allow_llm and needs_help and llm is not None and llm.available):
        return result

    prompt = (
        "You are classifying a domain name for a domain-investment research "
        "system.\n\n"
        f"Domain: {domain}\n"
        f"Parsed words: {words}\n"
        f"Deterministic category guess: "
        f"{result.category.value or 'none'}\n\n"
        "Classify the industry this name most plausibly belongs to, the search "
        "intent it implies, and whether its likely buyers are businesses or "
        "consumers. Use a single lowercase slug for the category. If the name "
        "is genuinely generic or meaningless, say category 'unclear' with low "
        "confidence. Do not speculate beyond the name itself."
    )
    try:
        raw = llm.complete_json("classify_domain", prompt, CLASSIFY_SCHEMA,
                                max_tokens=400)
    except LlmUnavailable:
        return result

    conf = float(raw.get("confidence", 0.0) or 0.0)
    category = str(raw.get("category", "")).strip().lower()
    reasoning = str(raw.get("reasoning", "")).strip() or None

    if category and category != "unclear" and (
            result.category.is_missing or conf > result.category.confidence):
        result.category = llm_inferred(category, "llm.classify", confidence=conf,
                                       note=reasoning)
    if result.intent_type.is_missing and raw.get("intent_type"):
        result.intent_type = llm_inferred(str(raw["intent_type"]), "llm.classify",
                                          confidence=conf, note=reasoning)
    if raw.get("audience"):
        result.audience = llm_inferred(str(raw["audience"]), "llm.classify",
                                       confidence=conf, note=reasoning)
    result.reasoning = reasoning
    return result
