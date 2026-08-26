"""Deterministic structural and linguistic feature extraction.

Everything in this module is DERIVED: pure functions of the domain string plus
the frozen lexicon. No network, no model, no randomness. The linguistic
"scores" (pronounceability, brandability, ...) are bounded 0..100 composites of
those deterministic parts, and each one records its own component breakdown so
the number can be taken apart later.

These are features, not judgements. They feed the valuation and probability
models; they are not themselves a verdict on a domain.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.scoring.lexicon import (count_syllables, is_word, looks_plural,
                                 segment, word_zipf)

FEATURES_VERSION = "f0.1.0"

VOWELS = set("aeiou")

# Below this pronounceability a name is treated as unsayable and its
# brandability is scaled down proportionally rather than merely docked points.
PRONOUNCEABILITY_FLOOR = 55.0

# Modifier words that signal "the good name was taken". Their presence is a
# quality signal about *this* name and a discovery signal for buyer matching:
# a company on getflow.com is a candidate buyer for flow.com.
GENERIC_MODIFIERS = {
    "get", "try", "use", "my", "the", "official", "app", "online", "group",
    "hq", "go", "join", "with", "team", "now", "web", "site", "shop", "store",
    "best", "top", "pro", "plus", "hub", "world", "direct", "central", "zone",
    "spot", "place", "find", "your", "our", "buy",
}

COMMON_PREFIXES = {"e", "i", "my", "go", "re", "un", "pre", "pro", "auto", "bio",
                   "geo", "neo", "tele", "micro", "macro", "multi", "super",
                   "ultra", "meta", "cyber", "smart", "quick", "easy", "true"}

COMMON_SUFFIXES = {"ly", "ify", "io", "hub", "labs", "lab", "works", "ware",
                   "soft", "tech", "wise", "base", "flow", "sync", "logic",
                   "matic", "ology", "ist", "eer", "er", "ing", "ify", "able"}

# Letter pairs and strings that create spelling ambiguity when dictated aloud.
AMBIGUOUS_PATTERNS = [
    (re.compile(r"(.)\1"), 1.0, "doubled letter"),
    (re.compile(r"ph"), 0.6, "ph/f ambiguity"),
    (re.compile(r"(ei|ie)"), 0.5, "ei/ie ambiguity"),
    (re.compile(r"[ck]{2}"), 0.5, "c/k ambiguity"),
    (re.compile(r"(z|x|q)"), 0.4, "uncommon letter"),
    (re.compile(r"(ough|augh)"), 0.9, "irregular vowel cluster"),
]

_CONSONANT_RUN_RE = re.compile(r"[^aeiouy]+")


def _clip(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


@dataclass
class DomainFeatureSet:
    """All deterministic features for one domain."""

    # structural
    length: int = 0
    sld_length: int = 0
    word_count: int = 0
    words: list[str] = field(default_factory=list)
    has_hyphen: bool = False
    has_digit: bool = False
    digit_count: int = 0
    hyphen_count: int = 0
    syllable_count: int = 0
    vowel_ratio: float = 0.0
    max_consonant_run: int = 0
    dictionary_word_count: int = 0
    all_words_dictionary: bool = False
    is_single_dictionary_word: bool = False
    is_plural: bool = False
    prefix: str | None = None
    suffix: str | None = None
    has_generic_modifier: bool = False
    acronym_likelihood: float = 0.0
    segmentation_confidence: float = 0.0
    mean_word_zipf: float = 0.0

    # linguistic composites, 0..100
    pronounceability: float = 0.0
    memorability: float = 0.0
    spelling_ambiguity: float = 0.0
    semantic_coherence: float = 0.0
    brandability: float = 0.0
    business_name_plausibility: float = 0.0

    components: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


# --------------------------------------------------------------------------
# structural
# --------------------------------------------------------------------------

def _acronym_likelihood(sld: str, words: tuple[str, ...], seg_conf: float) -> float:
    """0..1 estimate that the name is an acronym/initialism rather than words.

    Signals: short, low vowel ratio, does not segment into dictionary words.
    """
    core = re.sub(r"[^a-z]", "", sld)
    if not core:
        return 0.0
    if len(core) > 6:
        return 0.0
    vowels = sum(1 for c in core if c in VOWELS)
    vowel_ratio = vowels / len(core)
    if len(core) <= 4 and seg_conf < 0.75:
        base = 0.6
    elif len(core) <= 5 and seg_conf < 0.5:
        base = 0.45
    else:
        base = 0.1
    # Low vowel content is the strongest acronym tell (bkg, nyt, gsk).
    if vowel_ratio <= 0.2:
        base += 0.35
    elif vowel_ratio <= 0.34:
        base += 0.15
    # A single recognised word of reasonable length is not an acronym. Short
    # tokens are excluded from this discount because plenty of well-known
    # initialisms (ibm, bbc, cnn) are themselves corpus words.
    if len(words) == 1 and len(core) >= 4 and is_word(words[0]) and seg_conf >= 0.99:
        base -= 0.5
    return max(0.0, min(1.0, base))


def extract_structural(sld: str, tld: str) -> DomainFeatureSet:
    f = DomainFeatureSet()
    full = f"{sld}.{tld}"
    f.length = len(full)
    f.sld_length = len(sld)
    f.has_hyphen = "-" in sld
    f.hyphen_count = sld.count("-")
    f.digit_count = sum(1 for c in sld if c.isdigit())
    f.has_digit = f.digit_count > 0

    # Hyphens are explicit word boundaries; segment each piece separately.
    pieces = [p for p in sld.split("-") if p]
    tokens: list[str] = []
    conf_num = 0.0
    conf_den = 0
    for piece in pieces:
        alpha = re.sub(r"[^a-z]", "", piece)
        digits = re.sub(r"[^0-9]", "", piece)
        if alpha:
            toks, conf = segment(alpha)
            tokens.extend(toks)
            conf_num += conf * len(alpha)
            conf_den += len(alpha)
        if digits:
            tokens.append(digits)
    f.words = tokens
    f.word_count = len(tokens)
    f.segmentation_confidence = (conf_num / conf_den) if conf_den else 0.0

    alpha_words = [t for t in tokens if t.isalpha()]
    dict_words = [t for t in alpha_words if is_word(t)]
    f.dictionary_word_count = len(dict_words)
    f.all_words_dictionary = bool(alpha_words) and len(dict_words) == len(alpha_words)
    f.is_single_dictionary_word = (len(tokens) == 1 and bool(dict_words)
                                   and not f.has_digit and not f.has_hyphen)
    f.mean_word_zipf = (sum(word_zipf(w) for w in dict_words) / len(dict_words)
                        if dict_words else 0.0)
    f.is_plural = bool(alpha_words) and looks_plural(alpha_words[-1])

    f.syllable_count = sum(count_syllables(w) for w in alpha_words) or 0
    letters = [c for c in sld if c.isalpha()]
    f.vowel_ratio = (sum(1 for c in letters if c in VOWELS) / len(letters)) if letters else 0.0
    runs = _CONSONANT_RUN_RE.findall(re.sub(r"[^a-z]", "", sld))
    f.max_consonant_run = max((len(r) for r in runs), default=0)

    if alpha_words:
        first, last = alpha_words[0], alpha_words[-1]
        f.prefix = first if (len(alpha_words) > 1 and first in COMMON_PREFIXES) else None
        f.suffix = last if (len(alpha_words) > 1 and last in COMMON_SUFFIXES) else None
        f.has_generic_modifier = any(w in GENERIC_MODIFIERS for w in alpha_words)

    f.acronym_likelihood = _acronym_likelihood(sld, tuple(tokens), f.segmentation_confidence)
    return f


# --------------------------------------------------------------------------
# linguistic composites
# --------------------------------------------------------------------------

def _pronounceability(f: DomainFeatureSet, sld: str) -> tuple[float, dict]:
    """0..100. Penalises consonant pile-ups, missing vowels and length.

    Real English words are the reference point: a name made of them starts high
    and only loses points for length.
    """
    core = re.sub(r"[^a-z]", "", sld)
    if not core:
        return 0.0, {"reason": "no alphabetic content"}
    score = 100.0
    parts: dict[str, float] = {}

    # Vowel balance: English sits near 0.38. Deviation in either direction hurts.
    ideal = 0.38
    dev = abs(f.vowel_ratio - ideal)
    p_vowel = -min(40.0, dev * 130.0)
    parts["vowel_balance"] = round(p_vowel, 2)

    p_runs = -min(35.0, max(0, f.max_consonant_run - 3) * 12.0)
    parts["consonant_runs"] = round(p_runs, 2)

    p_len = -min(20.0, max(0, len(core) - 12) * 2.0)
    parts["length"] = round(p_len, 2)

    # Dictionary words are pronounceable by definition.
    coverage_bonus = 15.0 * f.segmentation_confidence
    parts["dictionary_coverage"] = round(coverage_bonus, 2)

    p_syll = -min(15.0, max(0, f.syllable_count - 4) * 5.0)
    parts["syllables"] = round(p_syll, 2)

    score = _clip(score + sum(parts.values()))
    return score, parts


def _spelling_ambiguity(sld: str) -> tuple[float, dict]:
    """0..100 where HIGH means MORE ambiguous (worse). "Can you spell that?" """
    core = re.sub(r"[^a-z]", "", sld)
    hits: dict[str, float] = {}
    total = 0.0
    for pattern, weight, label in AMBIGUOUS_PATTERNS:
        n = len(pattern.findall(core))
        if n:
            contribution = weight * n * 12.0
            hits[label] = round(contribution, 2)
            total += contribution
    if "-" in sld:
        hits["hyphen"] = 25.0
        total += 25.0
    if any(c.isdigit() for c in sld):
        # "4" vs "four" is the classic dictation failure.
        hits["digit"] = 20.0
        total += 20.0
    return _clip(total), hits


def _memorability(f: DomainFeatureSet, pronounceability: float,
                  ambiguity: float) -> tuple[float, dict]:
    """0..100. Short, pronounceable, familiar words, few of them."""
    parts = {
        "pronounceability": round(0.35 * pronounceability, 2),
        "brevity": round(_clip(100.0 - max(0, f.sld_length - 5) * 5.0) * 0.25, 2),
        "familiarity": round(_clip(f.mean_word_zipf / 6.0 * 100.0) * 0.20, 2),
        "few_words": round(_clip(100.0 - max(0, f.word_count - 1) * 28.0) * 0.20, 2),
        "ambiguity_penalty": round(-0.30 * ambiguity, 2),
    }
    return _clip(sum(parts.values())), parts


def _semantic_coherence(f: DomainFeatureSet) -> tuple[float, dict]:
    """0..100. Do the parts read as a phrase rather than a random collision?

    Deterministic proxy only: dictionary coverage, word count, and whether the
    name is dominated by filler modifiers. An LLM classifier can refine this
    (see ``app/scoring/classify.py``) but does not replace it.
    """
    parts: dict[str, float] = {}
    parts["dictionary_coverage"] = round(60.0 * f.segmentation_confidence, 2)
    if f.word_count == 0:
        parts["word_count"] = 0.0
    elif f.word_count <= 2:
        parts["word_count"] = 30.0
    elif f.word_count == 3:
        parts["word_count"] = 15.0
    else:
        parts["word_count"] = 0.0
    parts["modifier_penalty"] = -15.0 if f.has_generic_modifier else 0.0
    parts["defect_penalty"] = -10.0 * (int(f.has_hyphen) + int(f.has_digit))
    parts["acronym_penalty"] = round(-25.0 * f.acronym_likelihood, 2)
    parts["base"] = 10.0
    return _clip(sum(parts.values())), parts


def _brandability(f: DomainFeatureSet, pronounceability: float, memorability: float,
                  ambiguity: float) -> tuple[float, dict]:
    """0..100. Would this work as a company's actual name?

    Brandable is not the same as descriptive. Two short pronounceable words with
    low ambiguity brand well; four descriptive keywords do not, even though they
    may have better search intent.
    """
    parts = {
        "pronounceability": round(0.30 * pronounceability, 2),
        "memorability": round(0.30 * memorability, 2),
        "brevity": round(_clip(100.0 - max(0, f.sld_length - 8) * 6.0) * 0.20, 2),
        "ambiguity_penalty": round(-0.25 * ambiguity, 2),
    }
    bonus = 0.0
    if f.word_count <= 2 and not f.has_hyphen and not f.has_digit:
        bonus += 12.0
    if f.is_single_dictionary_word:
        bonus += 10.0
    if f.has_generic_modifier:
        bonus -= 8.0
    if f.word_count >= 4:
        bonus -= 15.0
    parts["structure_bonus"] = round(bonus, 2)
    score = _clip(sum(parts.values()))

    # Hard gate: an unpronounceable string is not brandable regardless of how
    # short and tidy it is. Invented-but-sayable names (zillow, kajabi) pass
    # this because their pronounceability is high even though they are not
    # dictionary words - which is exactly the distinction we want.
    if pronounceability < PRONOUNCEABILITY_FLOOR:
        gate = pronounceability / PRONOUNCEABILITY_FLOOR
        parts["unpronounceable_gate"] = round(gate, 3)
        score *= gate
    return _clip(score), parts


def _business_name_plausibility(f: DomainFeatureSet, brandability: float,
                                coherence: float) -> tuple[float, dict]:
    """0..100. Could a real company plausibly be *called* this?

    Distinct from brandability: 'berlinroofing' is a highly plausible business
    name and a mediocre brand.
    """
    parts = {
        "coherence": round(0.45 * coherence, 2),
        "brandability": round(0.25 * brandability, 2),
    }
    bonus = 0.0
    if f.all_words_dictionary and 1 <= f.word_count <= 3:
        bonus += 20.0
    if f.is_plural:
        bonus += 3.0
    if f.has_digit:
        bonus -= 12.0
    if f.has_hyphen:
        bonus -= 10.0
    if f.acronym_likelihood > 0.6:
        # Acronyms are plausible company names but are rarely *available*
        # meaningfully; keep the credit small.
        bonus += 5.0
    parts["structure_bonus"] = round(bonus, 2)
    return _clip(sum(parts.values())), parts


def extract_features(sld: str, tld: str) -> DomainFeatureSet:
    """Full deterministic feature extraction for one domain."""
    f = extract_structural(sld, tld)

    pron, pron_parts = _pronounceability(f, sld)
    amb, amb_parts = _spelling_ambiguity(sld)
    mem, mem_parts = _memorability(f, pron, amb)
    coh, coh_parts = _semantic_coherence(f)
    brand, brand_parts = _brandability(f, pron, mem, amb)
    plaus, plaus_parts = _business_name_plausibility(f, brand, coh)

    f.pronounceability = round(pron, 2)
    f.spelling_ambiguity = round(amb, 2)
    f.memorability = round(mem, 2)
    f.semantic_coherence = round(coh, 2)
    f.brandability = round(brand, 2)
    f.business_name_plausibility = round(plaus, 2)
    f.components = {
        "pronounceability": pron_parts,
        "spelling_ambiguity": amb_parts,
        "memorability": mem_parts,
        "semantic_coherence": coh_parts,
        "brandability": brand_parts,
        "business_name_plausibility": plaus_parts,
    }
    return f
