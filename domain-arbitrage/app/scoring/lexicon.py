"""English lexicon, word segmentation and syllable counting.

Backed by the ``wordfreq`` package, which ships corpus-derived word frequencies.
That gives us a real dictionary and a real notion of "how common is this word",
rather than a hand-typed word list. Frequencies are used for:

  * dictionary-word detection
  * segmenting a second-level domain into its constituent words
  * memorability / familiarity scoring

All of it is deterministic: same input, same output, no network, no model.
"""

from __future__ import annotations

import re
from functools import lru_cache

from wordfreq import top_n_list, zipf_frequency

# A token must clear this corpus frequency (Zipf scale: log10 occurrences per
# billion words) to count as a dictionary word. 2.6 excludes the long tail of
# typos, fragments and proper-noun debris in the frequency list while keeping
# ordinary vocabulary like "roofing" (3.2) and "telematics" (2.7).
MIN_ZIPF = 2.6
MIN_ZIPF_SHORT = 3.6      # 3-letter tokens must be genuinely common
MAX_WORD_LEN = 22

# Sum-of-log-probability segmentation. log10(P(token)) = zipf - 9, which is
# always negative, so adding tokens costs score. That is what stops the DP from
# shredding a name into a pile of tiny "words".
_LOG_PROB_OFFSET = 9.0
UNKNOWN_BASE_PENALTY = -11.0
UNKNOWN_PER_CHAR_PENALTY = -1.1

_VOCAB_SIZE = 120_000


@lru_cache(maxsize=1)
def vocabulary() -> frozenset[str]:
    """Common English words, frequency-filtered.

    Built once from the wordfreq corpus list. Membership is a set lookup, which
    matters because segmenting 10k domains issues millions of them.
    """
    out = set()
    for w in top_n_list("en", _VOCAB_SIZE):
        if not w.isalpha():
            continue
        z = zipf_frequency(w, "en")
        if len(w) >= 4 and z >= MIN_ZIPF:
            out.add(w)
        elif len(w) == 3 and z >= MIN_ZIPF_SHORT:
            out.add(w)
    return frozenset(out)


# Short tokens that are legitimately words or standard business abbreviations.
_ALLOWED_SHORT = {"a", "i", "go", "my", "we", "up", "on", "in", "at", "to", "be",
                  "do", "it", "us", "ai", "hr", "pr", "tv", "id", "ad", "ok",
                  "no", "so", "by", "of", "or", "if", "is", "an", "as", "me",
                  "he", "vr", "ar", "iq", "rx", "ev"}
# Fragments the corpus ranks highly but which are never a word inside a name.
_SEGMENT_STOPLIST = {"s", "t", "d", "ll", "re", "ve", "nt", "th", "er", "ing",
                     "ed", "es", "ly", "al", "ic", "en", "st", "nd", "rd"}


@lru_cache(maxsize=200_000)
def is_word(token: str) -> bool:
    """True if the token is a recognised English word for our purposes."""
    if not token or not token.isalpha():
        return False
    t = token.lower()
    if t in _SEGMENT_STOPLIST:
        return False
    if len(t) <= 2:
        return t in _ALLOWED_SHORT
    return t in vocabulary()


@lru_cache(maxsize=200_000)
def word_zipf(token: str) -> float:
    """Corpus frequency on the Zipf scale (roughly 0..8). 0 means unseen."""
    return zipf_frequency(token.lower(), "en")


def _token_log_prob(token: str) -> float:
    """Score for one token in the segmentation DP. Always negative."""
    if is_word(token):
        z = word_zipf(token)
        if z <= 0:
            z = MIN_ZIPF
        return z - _LOG_PROB_OFFSET
    return UNKNOWN_BASE_PENALTY + UNKNOWN_PER_CHAR_PENALTY * len(token)


@lru_cache(maxsize=100_000)
def segment(text: str) -> tuple[tuple[str, ...], float]:
    """Split a lowercase alphabetic string into its most probable word sequence.

    Standard unigram-language-model dynamic program: maximise the sum of token
    log-probabilities. Because every token contributes a negative score, a split
    only happens when it genuinely explains the string better.

    Returns ``(tokens, confidence)`` where confidence in 0..1 is the fraction of
    characters covered by recognised dictionary words.
    """
    text = text.lower()
    if not text:
        return (), 0.0
    n = len(text)
    best: list[float] = [float("-inf")] * (n + 1)
    back: list[int] = [0] * (n + 1)
    best[0] = 0.0

    for end in range(1, n + 1):
        for start in range(max(0, end - MAX_WORD_LEN), end):
            if best[start] == float("-inf"):
                continue
            total = best[start] + _token_log_prob(text[start:end])
            if total > best[end]:
                best[end] = total
                back[end] = start

    tokens: list[str] = []
    pos = n
    while pos > 0:
        start = back[pos]
        tokens.append(text[start:pos])
        pos = start
    tokens.reverse()

    covered = sum(len(t) for t in tokens if is_word(t))
    confidence = covered / n if n else 0.0
    return tuple(tokens), confidence


_VOWELS = set("aeiouy")
_VOWEL_GROUP_RE = re.compile(r"[aeiouy]+")


def count_syllables(word: str) -> int:
    """Heuristic English syllable count.

    Vowel-group counting with the standard silent-e and -le corrections. Good
    enough for a pronounceability feature; not a phonetic dictionary.
    """
    w = word.lower().strip()
    if not w or not w.isalpha():
        return 0
    groups = _VOWEL_GROUP_RE.findall(w)
    count = len(groups)
    if w.endswith("e") and not w.endswith(("le", "ee", "ye")) and count > 1:
        count -= 1
    if w.endswith("le") and len(w) > 2 and w[-3] not in _VOWELS:
        count += 1
    if w.endswith(("es", "ed")) and count > 1 and len(w) > 3 and w[-3] not in _VOWELS:
        count -= 1
    return max(1, count)


_PLURAL_EXCEPTIONS = {"news", "business", "class", "glass", "press", "series",
                      "gas", "bus", "campus", "status", "focus", "analysis",
                      "boss", "access", "process", "success", "address", "less",
                      "cross", "loss", "mass", "pass", "chess", "dress"}


def looks_plural(token: str) -> bool:
    t = token.lower()
    if t in _PLURAL_EXCEPTIONS or len(t) < 4:
        return False
    if t.endswith("ss") or t.endswith("us") or t.endswith("is"):
        return False
    if t.endswith("ies") and is_word(t[:-3] + "y"):
        return True
    if t.endswith("es") and is_word(t[:-2]):
        return True
    if t.endswith("s") and is_word(t[:-1]):
        return True
    return False
