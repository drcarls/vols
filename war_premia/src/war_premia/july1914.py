"""The July-1914 extension — and why the premium can't be estimated, or even read
off the raw bond quotes.

The Rigobon-Sack estimator needs a *war-week variance regime*: several war-week
observations whose elevated covariance identifies the factor. July 1914 denies it
that, on both assets, because the markets closed exactly when war came:

* **Short-term rates** end **1914-06-27** — the eve of Sarajevo (28 June). Every
  July-1914 war event falls *after* the data. Not estimable.
* **Long-term bonds** are monthly with a **63-day gap, 1914-06-03 → 1914-08-05**,
  straight across the crisis. A single observation spans it — no regime.

## The raw bond quotes cannot be read either (audit)

An earlier version of this module reported a June-3 → Aug-5 bond "cross-section"
(Consols −0.3%, French −1.8%, …) and read it as a trivially small, Ferguson-flat
move. **That reading was wrong and is withdrawn.** Pulling the raw column
(``bond_quote_audit``) shows why:

* The quotes are **prices** (points of par), not yields.
* The **June-3 baseline is ex-dividend** for Consols (76.75 on Jun 2 → 75.0 xd on
  Jun 3) and for the Russian 1822 — a mechanical coupon drop, not a market move.
* The **post-closure quotes are not genuine trades.** Russian and Austrian bonds
  *rise* from August to September 1914 (Austrian Gold 84→89, Russian 1822
  120→125) — impossible for belligerent debt at war. They are nominal/administered
  quotes carried through the closure. Comparing a stale August quote to an
  ex-dividend June baseline produced the spurious ~2%.

So the bond cross-section is **uninterpretable** — a lower bound that isn't even
a bound, because the endpoints aren't real prices.

## The one genuine signal

The workbook's own NOTES sheet records the last real pre-closure move: the London
price of the **French 3% rente fell from 80 to 76.5 on 30 July 1914 — about
−4.4% in that final trading week**, and accelerating. Together with the money
market (Bank of England rate 3 → 4 → 8 → 10% the same week; see the Chronicle
extension), that is a market **routing as it shut**, not a flat market. The full
war shock is simply unobservable: trading stopped mid-repricing.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from neal_weidenmier.load import true_date

D = datetime.date

# RAW-sheet (price column, ex-dividend-flag column) per sovereign.
SOVEREIGN_COLS: Dict[str, Tuple[int, Optional[int]]] = {
    "UK Consols 3%": (3, 4),
    "French 3% rente (Paris)": (7, None),
    "Russian New 4%": (15, 14),
    "Russian 1822 5%": (16, 17),
    "Austrian Gold 4%": (24, None),
    "German Imperial 3%": (28, 27),
    "Prussian Consols 3.5%": (33, 36),
}

BELLIGERENT = {"Russian New 4%", "Russian 1822 5%", "Austrian Gold 4%",
               "German Imperial 3%"}

CLEAN_PRE = D(1914, 6, 2)      # last clean (cum-dividend) pre-crisis quote
EXDIV_PRE = D(1914, 6, 3)      # the ex-dividend quote used, wrongly, before
POST_STALE = D(1914, 8, 5)     # first post-closure quote (nominal)
POST_SEPT = D(1914, 9, 1)      # a later post-closure quote (still nominal)

# The one genuine pre-closure move, from the workbook's NOTES sheet.
GENUINE_SIGNAL = (
    "French 3% rente (London): 80.0 -> 76.5 by 30 July 1914 (~-4.4% in the final "
    "trading week), per the workbook NOTES sheet — a rout beginning as the market shut."
)


@dataclass(frozen=True)
class BondAudit:
    sovereign: str
    clean_pre: Optional[float]      # Jun 2 (cum-dividend)
    exdiv_pre: Optional[float]      # Jun 3 (ex-dividend)
    exdiv_flag: bool
    post_stale: Optional[float]     # Aug 5
    post_sept: Optional[float]      # Sep 1
    genuine: bool                   # False if a belligerent bond rises post-closure
    reason: str


def _raw(path: str):
    import xlrd

    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_name("RAW")
    rows: Dict[D, int] = {}
    for r in range(6, sh.nrows):
        c = sh.cell(r, 0)
        if c.ctype == 3:
            rows[true_date(xlrd.xldate.xldate_as_datetime(c.value, wb.datemode).date())] = r
    return wb, sh, rows


def bond_quote_audit(bonds_path: str) -> List[BondAudit]:
    """Audit the raw bond quotes across the closure: ex-dividend baseline and
    non-genuine (belligerent-bonds-rising) post-closure quotes."""
    import xlrd

    _wb, sh, rows = _raw(bonds_path)

    def val(d: D, col: Optional[int]) -> Optional[float]:
        r = rows.get(d)
        if r is None or col is None:
            return None
        cell = sh.cell(r, col)
        return float(cell.value) if cell.ctype == xlrd.XL_CELL_NUMBER else None

    out: List[BondAudit] = []
    for name, (pc, xc) in SOVEREIGN_COLS.items():
        clean = val(CLEAN_PRE, pc)
        exd = val(EXDIV_PRE, pc)
        xd_cell = sh.cell(rows[EXDIV_PRE], xc) if (xc and EXDIV_PRE in rows) else None
        exdiv = bool(xd_cell and "xd" in str(xd_cell.value).lower())
        stale = val(POST_STALE, pc)
        sept = val(POST_SEPT, pc)
        genuine = True
        reason = "post-closure quote suspect (market shut 31 July)"
        if name in BELLIGERENT and stale is not None and sept is not None and sept > stale:
            genuine = False
            reason = f"belligerent bond RISES {stale}->{sept} Aug->Sep 1914 — not a real trade"
        out.append(BondAudit(name, clean, exd, exdiv, stale, sept, genuine, reason))
    return out


# ---- feasibility (unchanged; the estimator genuinely can't run) ----

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
    from neal_weidenmier.load import load_short_rates

    from .warweeks import JULY_1914_EVENTS, JULY_1914_SHORT_WINDOW, war_mask

    obs = load_short_rates(short_path)
    lo, hi = JULY_1914_SHORT_WINDOW
    sat = sorted({o.date for o in obs if lo <= o.date <= hi})
    mask = war_mask(sat, JULY_1914_EVENTS)
    return Feasibility(
        asset="short-term rates", n_obs=len(sat), n_war_weeks=sum(mask),
        last_obs=sat[-1] if sat else None, gap_across_crisis_days=None,
        estimable=False,
        reason=(f"data ends {sat[-1] if sat else '—'}, before the July war weeks; "
                f"{sum(mask)} boundary war-week, no crisis response"),
    )


def bond_feasibility(bonds_path: str) -> Feasibility:
    _wb, _sh, rows = _raw(bonds_path)
    ds = sorted(rows)
    gap = None
    for i in range(1, len(ds)):
        if ds[i] >= POST_STALE and ds[i - 1] < POST_STALE:
            gap = (ds[i] - ds[i - 1]).days   # last pre-closure quote -> first post
            break
    return Feasibility(
        asset="long-term bonds", n_obs=len(ds), n_war_weeks=0,
        last_obs=ds[-1] if ds else None, gap_across_crisis_days=gap, estimable=False,
        reason=(f"monthly with a {gap}-day gap {CLEAN_PRE}->{POST_STALE} across the crisis; "
                "and the post-closure quotes are nominal, not trades (see bond_quote_audit)"),
    )
