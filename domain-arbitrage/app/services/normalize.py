"""Domain normalisation and deduplication.

Normalisation is deterministic and lossless in the sense that the original
string is always kept on the listing's ``raw_row``. Anything that cannot be
normalised is *rejected with a reason*, never silently coerced.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Multi-label public suffixes we care about. Not the full Public Suffix List -
# adding `publicsuffix2` is the right move for production, and is noted in the
# README under missing data sources. Everything not listed falls back to "last
# label is the TLD", which is correct for the overwhelming majority of
# aftermarket inventory.
MULTI_LABEL_SUFFIXES = {
    "co.uk", "org.uk", "me.uk", "ltd.uk", "plc.uk", "net.uk", "sch.uk", "ac.uk",
    "gov.uk", "com.au", "net.au", "org.au", "edu.au", "gov.au", "co.nz",
    "net.nz", "org.nz", "co.za", "org.za", "com.br", "net.br", "com.mx",
    "com.ar", "co.jp", "or.jp", "ne.jp", "co.kr", "com.cn", "net.cn", "org.cn",
    "com.sg", "com.hk", "co.in", "net.in", "org.in", "com.tr", "co.il",
    "com.my", "co.id", "com.ph", "com.vn", "com.tw", "com.pl", "com.ua",
}

_LABEL_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")
_SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*://", re.IGNORECASE)


@dataclass(frozen=True)
class NormalizedDomain:
    name: str            # ascii, lowercase, punycode if IDN
    sld: str             # second-level label only
    tld: str             # public suffix, no leading dot
    is_idn: bool
    unicode_name: str | None
    original: str


class NormalizationError(ValueError):
    """Raised with a human-readable reason so the import can report it."""


def split_public_suffix(labels: list[str]) -> tuple[str, str]:
    """Return (sld, suffix) given the label list of a hostname."""
    if len(labels) >= 3:
        candidate = ".".join(labels[-2:])
        if candidate in MULTI_LABEL_SUFFIXES:
            return labels[-3], candidate
    return labels[-2], labels[-1]


def normalize_domain(raw: str) -> NormalizedDomain:
    """Normalise a user-supplied domain string.

    Handles: surrounding whitespace, scheme prefixes, ``www.``, trailing dots,
    uppercase, trailing paths/queries, and internationalised names (converted to
    punycode, with the unicode form retained).
    """
    if raw is None:
        raise NormalizationError("empty value")
    text = str(raw).strip()
    if not text:
        raise NormalizationError("empty value")

    text = _SCHEME_RE.sub("", text)
    text = text.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    text = text.split("@")[-1]           # tolerate an email-looking cell
    text = text.split(":", 1)[0]         # strip port
    text = text.strip().strip(".").lower()
    if not text:
        raise NormalizationError("empty after cleanup")

    unicode_name: str | None = None
    is_idn = not text.isascii()
    if is_idn:
        unicode_name = text
        try:
            text = text.encode("idna").decode("ascii")
        except Exception as exc:  # noqa: BLE001 - want the reason in the report
            raise NormalizationError(f"invalid internationalised name: {exc}") from exc

    if text.startswith("www."):
        text = text[4:]

    labels = text.split(".")
    if len(labels) < 2:
        raise NormalizationError("no TLD present")
    for label in labels:
        if not label:
            raise NormalizationError("empty label")
        if not _LABEL_RE.match(label):
            raise NormalizationError(f"invalid label {label!r}")
    if len(text) > 253:
        raise NormalizationError("name exceeds 253 characters")

    sld, tld = split_public_suffix(labels)
    return NormalizedDomain(name=f"{sld}.{tld}", sld=sld, tld=tld, is_idn=is_idn,
                            unicode_name=unicode_name, original=str(raw))


def dedupe(names: list[str]) -> tuple[list[str], dict[str, int]]:
    """Deduplicate normalised names, preserving first-seen order."""
    seen: dict[str, int] = {}
    order: list[str] = []
    for n in names:
        if n in seen:
            seen[n] += 1
        else:
            seen[n] = 1
            order.append(n)
    duplicates = {k: v for k, v in seen.items() if v > 1}
    return order, duplicates
