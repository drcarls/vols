"""The July-1914 extension — and why the premium can't be estimated the same way.

The Rigobon-Sack estimator needs a *war-week variance regime*: several war-week
observations whose elevated covariance identifies the factor. July 1914 denies it
that, on both assets, because the markets closed exactly when war came:

* **Short-term rates** end **1914-06-27** — the eve of Sarajevo (28 June). Every
  July-1914 war event falls *after* the data, so the window holds at most the one
  boundary week and no crisis response. Not estimable.
* **Long-term bonds** are monthly and have a **63-day gap, 1914-06-03 → 1914-08-05**,
  straight across the crisis. A single observation spans it — no regime to form.

What *is* observable is that one bond change across the gap. It is not a
heteroskedasticity premium and it is a **distorted lower bound** (closure and
support operations froze quoted prices). It carries **two readings, and both must
be stated**:

* **Ordering (the smaller point):** the belligerents' bonds fell most (French,
  German, Russian ~2%) while British Consols barely moved (−0.3%) — the paper's
  belligerent-vs-safe-haven cross-section, at the moment war came.
* **Magnitude (the larger point — Ferguson's):** a ~2% fall on the *outbreak of a
  world war* is almost nothing. The bond market did not price the war, even as it
  began. This is Ferguson's finding — the markets were caught off guard — and it
  is the headline, not a refutation of it. The ordering rides on top of a shock
  that is, in absolute terms, trivially small.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional

from neal_weidenmier.load import true_date

D = datetime.date

# RAW-sheet columns of the long-term bond workbook -> readable sovereign labels.
SOVEREIGN_COLS: Dict[int, str] = {
    3: "UK Consols 3%",
    7: "French 3% rentes",
    15: "Russian 4% (ser. II)",
    16: "Russian 1822 5%",
    24: "Austrian Gold 4%",
    28: "German Imperial 3%",
    33: "Prussian Consols 3.5%",
}

PRE_CRISIS = D(1914, 6, 3)     # last quote before the closure gap
POST_OUTBREAK = D(1914, 8, 5)  # first quote after war began


@dataclass(frozen=True)
class BondChange:
    label: str
    pre: float
    post: float

    @property
    def pct(self) -> float:
        return 100.0 * (self.post - self.pre) / self.pre if self.pre else float("nan")


def _raw_rows(path: str):
    import xlrd

    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_name("RAW")
    rows: Dict[D, int] = {}
    for r in range(6, sh.nrows):
        c = sh.cell(r, 0)
        if c.ctype == 3:
            d = true_date(__import__("xlrd").xldate.xldate_as_datetime(c.value, wb.datemode).date())
            rows[d] = r
    return wb, sh, rows


def crisis_bond_change(
    bonds_path: str, *, pre: D = PRE_CRISIS, post: D = POST_OUTBREAK
) -> List[BondChange]:
    """The one bond price change spanning the 1914 closure, per sovereign."""
    import xlrd

    _wb, sh, rows = _raw_rows(bonds_path)
    out: List[BondChange] = []
    rp, rq = rows.get(pre), rows.get(post)
    if rp is None or rq is None:
        return out
    for col, label in SOVEREIGN_COLS.items():
        cp, cq = sh.cell(rp, col), sh.cell(rq, col)
        if cp.ctype == xlrd.XL_CELL_NUMBER and cq.ctype == xlrd.XL_CELL_NUMBER:
            out.append(BondChange(label, float(cp.value), float(cq.value)))
    return out


@dataclass(frozen=True)
class Feasibility:
    asset: str
    n_obs: int
    n_war_weeks: int
    last_obs: Optional[D]
    gap_across_crisis_days: Optional[int]
    estimable: bool
    reason: str


def short_rate_feasibility(short_path: str) -> Feasibility:
    """Why the July-1914 premium is not estimable on the short-term rates."""
    from neal_weidenmier.load import load_short_rates

    from .warweeks import JULY_1914_EVENTS, JULY_1914_SHORT_WINDOW, war_mask

    obs = load_short_rates(short_path)
    lo, hi = JULY_1914_SHORT_WINDOW
    sat = sorted({o.date for o in obs if lo <= o.date <= hi})
    mask = war_mask(sat, JULY_1914_EVENTS)
    nwar = sum(mask)
    return Feasibility(
        asset="short-term rates",
        n_obs=len(sat),
        n_war_weeks=nwar,
        last_obs=sat[-1] if sat else None,
        gap_across_crisis_days=None,
        estimable=False,
        reason=(f"data ends {sat[-1] if sat else '—'}, before the July war weeks; "
                f"only {nwar} boundary war-week and no crisis response"),
    )


def bond_feasibility(bonds_path: str) -> Feasibility:
    """Why the July-1914 premium is not estimable on the long-term bonds."""
    _wb, _sh, rows = _raw_rows(bonds_path)
    ds = sorted(rows)
    gap = None
    # The crisis gap is the consecutive pair straddling the closure:
    # last quote on/before PRE_CRISIS -> first quote on/after POST_OUTBREAK.
    for i in range(1, len(ds)):
        if ds[i - 1] <= PRE_CRISIS and ds[i] >= POST_OUTBREAK:
            gap = (ds[i] - ds[i - 1]).days
            break
    return Feasibility(
        asset="long-term bonds",
        n_obs=len(ds),
        n_war_weeks=0,
        last_obs=ds[-1] if ds else None,
        gap_across_crisis_days=gap,
        estimable=False,
        reason=(f"monthly with a {gap}-day gap {PRE_CRISIS}->{POST_OUTBREAK} across the "
                "crisis; a single observation spans it — no variance regime"),
    )
