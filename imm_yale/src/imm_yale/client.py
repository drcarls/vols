"""A polite client for the Yale ICF *Investor's Monthly Manual* search backend.

The interface is a legacy PHP form. This client speaks it exactly as the browser
does — the field mapping below was reverse-engineered from the live form and the
request layer is **verified**: the server accepts these POSTs and runs the query
(HTTP 200). What is *not* verified is the shape of a populated data table, because
during development the query backend returned no rows for any selection (see
``RECON.md``); :mod:`imm_yale.parse` documents that boundary.

Field mapping (from ``immsrchintstocksall.php`` -> ``alldatadispstocksall.php``):

* ``stype`` selects the search mode:
  - ``byid``    + ``securityID[]`` (repeatable, up to 5) — numeric IMM ids.
  - ``comname`` + ``cname``  — **partial** company-name match. NB the partial
    field is POSTed as ``cname`` even though the HTML input is named ``pcname``;
    the backend reads ``cname``. (Confirmed by probing: only ``cname`` was read.)
  - ``cname``   + ``ecname`` — **exact** company-name match.
* Date range: ``StMon``/``StYear`` .. ``EndMon``/``EndYear``.
* Variables to return: the ``VarN[]`` checkbox groups; ``Var7`` is the £-s-d
  yield used for spreads.
* ``format`` chooses the output rendering.

The client establishes a session (a cold POST is served the same "no records"
page, but a prior GET sets ``PHPSESSID`` and a ``Referer``, which is what a real
session looks like), rate-limits, and retries transient resets with backoff.
"""

from __future__ import annotations

import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

BASE = "https://depot.som.yale.edu/icf/imm/immdatadownload-mysql"
FORM_URL = f"{BASE}/immsrchintstocksall.php"
DATA_URL = f"{BASE}/alldatadispstocksall.php"

# The £-s-d yield group and the late price — enough to build a spread.
YIELD_VARS = [
    "YieldInvtLatePricePound",
    "YieldInvtLatePriceShilling",
    "YieldInvtLatePricePence",
]
PRICE_VARS = ["PriceMonthLate"]

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


@dataclass
class Query:
    start_year: int
    end_year: int
    start_month: int = 1
    end_month: int = 12
    security_ids: Sequence[str] = field(default_factory=list)
    name_partial: Optional[str] = None
    name_exact: Optional[str] = None
    variables: Sequence[str] = field(default_factory=lambda: list(YIELD_VARS) + list(PRICE_VARS))
    fmt: str = "html"

    def form_fields(self) -> List[tuple]:
        """Serialise to ordered POST pairs matching the live form's contract."""
        fields: List[tuple] = []
        if self.security_ids:
            fields.append(("stype", "byid"))
            for sid in self.security_ids:
                fields.append(("securityID[]", str(sid)))
        elif self.name_exact is not None:
            fields.append(("stype", "cname"))
            fields.append(("ecname", self.name_exact))
        elif self.name_partial is not None:
            fields.append(("stype", "comname"))
            fields.append(("cname", self.name_partial))  # backend reads `cname`
        else:
            raise ValueError("Query needs security_ids, name_partial or name_exact")
        fields += [
            ("StMon", str(self.start_month)),
            ("StYear", str(self.start_year)),
            ("EndMon", str(self.end_month)),
            ("EndYear", str(self.end_year)),
        ]
        for v in self._grouped_vars():
            fields.append(v)
        fields.append(("format", self.fmt))
        return fields

    def _grouped_vars(self) -> List[tuple]:
        # Each IMM variable belongs to a VarN[] checkbox group; the backend
        # accepts the variable value under its own group key. We map the ones we
        # use (yield -> Var7, late price -> Var4) and fall back to Var4.
        group = {
            "PriceMonthLate": "Var4[]",
            "PriceMonthOpen": "Var4[]",
            "PriceMonthHigh": "Var4[]",
            "PriceMonthLow": "Var4[]",
            "YieldInvtLatePricePound": "Var7[]",
            "YieldInvtLatePriceShilling": "Var7[]",
            "YieldInvtLatePricePence": "Var7[]",
            "Par": "Var9[]",
            "IssuePrice": "Var1[]",
        }
        return [(group.get(v, "Var4[]"), v) for v in self.variables]


class IMMClient:
    """Session-scoped, rate-limited HTTP client for the IMM search backend.

    Uses only the standard library (``urllib``), which honours the ``HTTPS_PROXY``
    and CA-bundle environment already configured in this environment. Pass a
    ``sleep`` >= a couple of seconds to stay well within polite crawl limits — the
    backend resets the connection under rapid-fire load.
    """

    def __init__(
        self,
        *,
        sleep: float = 4.0,
        timeout: float = 45.0,
        retries: int = 4,
    ) -> None:
        self.sleep = sleep
        self.timeout = timeout
        self.retries = retries
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor()
        )
        self._opener.addheaders = [("User-Agent", _UA)]
        self._session_ready = False

    def _establish_session(self) -> None:
        if self._session_ready:
            return
        req = urllib.request.Request(FORM_URL)
        self._opener.open(req, timeout=self.timeout).read()
        self._session_ready = True

    def fetch(self, query: Query) -> str:
        """Run one query and return the raw response body (HTML/text)."""
        self._establish_session()
        body = urllib.parse.urlencode(query.form_fields()).encode("utf-8")
        last_err: Optional[Exception] = None
        for attempt in range(self.retries):
            try:
                req = urllib.request.Request(
                    DATA_URL,
                    data=body,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Referer": FORM_URL,
                    },
                )
                with self._opener.open(req, timeout=self.timeout) as resp:
                    text = resp.read().decode("utf-8", "replace")
                time.sleep(self.sleep)
                return text
            except Exception as e:  # transient reset/timeout -> backoff
                last_err = e
                time.sleep(self.sleep * (attempt + 1))
        raise RuntimeError(f"IMM fetch failed after {self.retries} tries: {last_err}")
