"""Fee label -> canonical category.

Operators rename fees constantly, and the renaming is itself a finding: a
"convenience fee" that becomes an "order processing fee" between sweeps is the
same charge wearing a different coat. So classification is deliberately shallow
and auditable -- a visible pattern table rather than a model -- and the raw label
is always retained alongside the category.

Anything unmatched lands in OTHER, which is a work queue. A rising OTHER rate
means the table is stale, not that the fees are exotic.
"""

from __future__ import annotations

import re

from .model import FeeCategory

#: Order matters: the first match wins, so the more specific patterns lead.
_PATTERNS: tuple[tuple[FeeCategory, re.Pattern[str]], ...] = (
    (FeeCategory.ORDER_PROCESSING, re.compile(r"\border\s+(processing|handling)\b")),
    (FeeCategory.SMALL_ORDER, re.compile(r"\bsmall[-\s]?(order|cart|basket)\b")),
    (FeeCategory.REGULATORY_RECOVERY, re.compile(r"\bregulatory\b|\bcompliance\s+surcharge\b")),
    (FeeCategory.CONCESSION_RECOVERY, re.compile(r"\bconcession\s+(recovery|recoup)")),
    (FeeCategory.FACILITY, re.compile(r"\b(customer\s+)?facilit(y|ies)\b|\bvenue\s+fee\b")),
    (FeeCategory.RESORT, re.compile(r"\bresort\b|\bamenit(y|ies)\s+fee\b")),
    (FeeCategory.DESTINATION, re.compile(r"\bdestination\b|\burban\s+fee\b")),
    (FeeCategory.CLEANING, re.compile(r"\bclean(ing)?\b|\bhousekeeping\b|\bturnover\b")),
    (FeeCategory.RESERVATION, re.compile(r"\breservation\b|\bbooking\s+fee\b")),
    (FeeCategory.TRANSACTION, re.compile(r"\btransaction\b")),
    (FeeCategory.CONVENIENCE, re.compile(r"\bconvenience\b")),
    (FeeCategory.DELIVERY, re.compile(r"\bdeliver(y|ies)\b|\bcourier\b")),
    (FeeCategory.SERVICE, re.compile(r"\bservice\s+(fee|charge)\b|\bservice\b")),
    (FeeCategory.PROCESSING, re.compile(r"\bprocess(ing)?\b|\bfulfil?lment\b")),
    # Taxes and shipping are statutorily excluded from the all-in requirement, so
    # they must be recognised to avoid manufacturing violations out of them.
    (FeeCategory.TAX, re.compile(r"\btax(es)?\b|\bvat\b|\bgst\b|\boccupancy\b|\blodging\s+tax\b")),
    (FeeCategory.SHIPPING, re.compile(r"\bship(ping)?\b|\bpostage\b|\bfreight\b")),
)


def classify(raw_label: str) -> FeeCategory:
    """Map a displayed fee label to a canonical category."""
    text = raw_label.strip().lower()
    for category, pattern in _PATTERNS:
        if pattern.search(text):
            return category
    return FeeCategory.OTHER


def unclassified_rate(labels: list[str]) -> float:
    """Share of labels falling through to OTHER.

    Tracked per sweep. A rise means the pattern table needs attention before the
    next report goes out, since an unclassified mandatory fee still counts toward
    the gap but cannot be matched to a fact pattern.
    """
    if not labels:
        return 0.0
    other = sum(1 for label in labels if classify(label) is FeeCategory.OTHER)
    return other / len(labels)
