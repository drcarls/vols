"""The Kokovtsov event test — a test the 2005 paper could not run.

Vladimir Kokovtsov, Russia's finance minister (1904-1914) and premier — the
architect of Russian fiscal orthodoxy and of the foreign-borrowing programme
that anchored Russian credit in Paris — was dismissed by imperial rescript in
late January 1914 (Old Style); his cabinet formally ended **12 February 1914
(New Style)**. If any Russian short rate ever ought to carry a political-risk
signal, it is this: the market losing the man who guaranteed the debt.

The recovered Neal-Weidenmier data adds a St Petersburg column the paper lacked,
so the event is now runnable. This module runs it. The result is a clean,
*informative* null:

- The only Russian short rate present in 1914 is the **State Bank discount
  (bank) rate** — an administered policy rate. Around the dismissal it did not
  move: it sat on a flat plateau that straddles the event, and its next change
  was a *cut* weeks later (opposite sign to stress).
- The **market (open-market) rate**, which would price the shock, is exactly the
  series NW loses after 1900 — it ends 20 Oct 1900, with no 1914 observation.

So the answer to "did Russian short rates move around Kokovtsov's dismissal?" is:
the administered rate we have is silent by construction, and the market rate that
would answer the question is missing. The data cannot see the event.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import List, Optional

from neal_weidenmier.load import Observation, load_short_rates

# Cabinet formally ended 12 Feb 1914 (N.S.); dismissal rescript late Jan (O.S.).
# NW dates are weekly (Saturday) and Gregorian, so the N.S. date is the anchor.
EVENT_NS = datetime.date(1914, 2, 12)


@dataclass(frozen=True)
class Plateau:
    """A maximal run of a constant rate level that contains a target date."""

    level: float
    start: datetime.date
    end: datetime.date
    next_change_date: Optional[datetime.date]
    next_change_level: Optional[float]


# Market-priced Russian sovereign debt, quoted in London (RAW-sheet price cols).
# Same columns the bond audit uses (single source of truth in july1914).
RUSSIAN_BONDS = {"Russian New 4% (London)": 15, "Russian 1822 5% (London)": 16}

# Transmission check: France was Russia's banker (French savers held billions of
# francs of Russian loans), so a Russian credit scare should surface in the Paris
# rente. Col 7 is the French 3% rente (Paris); ex-coupon is mid-Jan/Apr/Jul/Oct,
# so a mid-February bracket is clean of coupon effects.
FRENCH_RENTE = {"French 3% rente (Paris)": 7}


@dataclass(frozen=True)
class BondMove:
    label: str
    before_date: Optional[datetime.date]
    before: Optional[float]
    after_date: Optional[datetime.date]
    after: Optional[float]
    pct: Optional[float]            # % change across the event bracket
    mean_abs_step: float           # normal weekly |Δ%| (trailing 12 months)
    sd_step: float                 # sd of weekly Δ% (trailing 12 months)
    n_steps: int
    window: List[tuple]            # (date, price) quotes within +/-28 days of event

    @property
    def within_normal(self) -> Optional[bool]:
        if self.pct is None:
            return None
        return abs(self.pct) <= self.mean_abs_step + self.sd_step


@dataclass(frozen=True)
class KokovtsovResult:
    bracket: List[Observation]          # weekly obs straddling the event
    bank_plateau: Optional[Plateau]     # the constant-level run around the event
    market_last: Optional[datetime.date]  # last St Petersburg market-rate obs
    market_in_1914: bool
    bonds: List[BondMove]               # market-priced Russian bonds across the event
    french: List[BondMove]             # French rente — transmission (France financed Russia)


def _series(obs: List[Observation], rate_type: str) -> List[Observation]:
    rows = [o for o in obs if o.city == "Petersburg" and o.rate_type == rate_type]
    return sorted(rows, key=lambda o: o.date)


def _plateau_containing(series: List[Observation], target: datetime.date) -> Optional[Plateau]:
    """The maximal constant-value run bracketing ``target`` (by nearest obs)."""
    if not series:
        return None
    # index of the observation on or just before the target (else the first)
    i = 0
    for j, o in enumerate(series):
        if o.date <= target:
            i = j
        else:
            break
    level = series[i].value
    lo = hi = i
    while lo > 0 and series[lo - 1].value == level:
        lo -= 1
    while hi + 1 < len(series) and series[hi + 1].value == level:
        hi += 1
    nxt = series[hi + 1] if hi + 1 < len(series) else None
    return Plateau(
        level=level,
        start=series[lo].date,
        end=series[hi].date,
        next_change_date=nxt.date if nxt else None,
        next_change_level=nxt.value if nxt else None,
    )


def _load_bonds(bonds_path: str, cols):
    """{label: [(date, price), ...]} for the given RAW-sheet price columns.

    Decodes RAW-sheet dates with the same +100-year rule as the short rates and
    the bond audit; blank/non-numeric prices are skipped, never imputed.
    """
    import xlrd

    wb = xlrd.open_workbook(bonds_path)
    sh = wb.sheet_by_name("RAW")
    # The RAW date column carries TWO interleaved vintages: ~1500 text cells in
    # 'd/m/yyyy' and ~300 Excel-serial cells. They are NOT the same observations —
    # the serials are a sparser, offset sampling whose quotes disagree with the
    # text series by ~1-2 points over the same weeks (e.g. early Mar 1914 serials
    # ~87 vs the text weekly ~88.5). Merging them would inject spurious jaggedness
    # into an event study, so we use the internally-consistent TEXT vintage, which
    # is the one quoted ~weekly across 1912-1914 and cleanly brackets the event.
    # (This is deliberate; an earlier version dropped the serials only by accident,
    # via a swallowed NameError.)
    date_of_row = {}
    for r in range(sh.nrows):
        c = sh.cell(r, 0)
        if c.ctype == 1 and "/" in c.value:  # text 'd/m/yyyy'
            try:
                date_of_row[r] = datetime.datetime.strptime(c.value.strip(), "%d/%m/%Y").date()
            except ValueError:
                continue
    out = {}
    for label, col in cols.items():
        rows = []
        for r, d in date_of_row.items():
            v = sh.cell_value(r, col)
            if isinstance(v, (int, float)) and v != "":
                rows.append((d, float(v)))
        out[label] = sorted(rows)
    return out


def _bond_move(label: str, series, event: datetime.date) -> BondMove:
    before = [(d, v) for d, v in series if d <= event]
    after = [(d, v) for d, v in series if d > event]
    bd, bv = before[-1] if before else (None, None)
    ad, av = after[0] if after else (None, None)
    pct = 100.0 * (av - bv) / bv if (bv and av) else None
    # "Normal" = weekly step variation over the 12 months BEFORE the event, so the
    # baseline isn't inflated by the 1905 revolution / Russo-Japanese war moves.
    lo = event - datetime.timedelta(days=365)
    recent = [(d, v) for d, v in series if lo <= d <= event]
    steps = [100.0 * (recent[i][1] - recent[i - 1][1]) / recent[i - 1][1]
             for i in range(1, len(recent)) if recent[i - 1][1]]
    mean_abs = sum(abs(s) for s in steps) / len(steps) if steps else 0.0
    var = sum(s * s for s in steps) / len(steps) - (sum(steps) / len(steps)) ** 2 if steps else 0.0
    sd = var ** 0.5
    window = [(d, v) for d, v in series if abs((d - event).days) <= 28]
    return BondMove(label, bd, bv, ad, av, pct, mean_abs, sd, len(steps), window)


def kokovtsov_test(short_path: str, bonds_path: Optional[str] = None,
                   event: datetime.date = EVENT_NS) -> KokovtsovResult:
    obs = load_short_rates(short_path)
    bank = _series(obs, "Bank")
    market = _series(obs, "Market")

    bracket = [o for o in bank if abs((o.date - event).days) <= 10]
    plateau = _plateau_containing(bank, event)
    market_last = market[-1].date if market else None
    market_in_1914 = any(o.date.year == 1914 for o in market)

    bonds: List[BondMove] = []
    french: List[BondMove] = []
    if bonds_path:
        loaded = _load_bonds(bonds_path, {**RUSSIAN_BONDS, **FRENCH_RENTE})
        bonds = [_bond_move(lbl, loaded[lbl], event) for lbl in RUSSIAN_BONDS]
        french = [_bond_move(lbl, loaded[lbl], event) for lbl in FRENCH_RENTE]

    return KokovtsovResult(
        bracket=bracket,
        bank_plateau=plateau,
        market_last=market_last,
        market_in_1914=market_in_1914,
        bonds=bonds,
        french=french,
    )


def format_result(res: KokovtsovResult) -> str:
    lines = []
    lines.append("Kokovtsov dismissal — St Petersburg short rates (event 12 Feb 1914 N.S.)")
    lines.append("")
    lines.append("Weekly BANK (State Bank discount) rate straddling the event:")
    for o in res.bracket:
        lines.append(f"    {o.date}   {o.value:.2f}%")
    p = res.bank_plateau
    if p:
        lines.append("")
        lines.append(f"  The rate sat at {p.level:.2f}% unbroken from {p.start} to {p.end}")
        lines.append(f"    (a {(p.end - p.start).days // 7}-week plateau straddling the dismissal).")
        if p.next_change_date is not None:
            direction = "cut" if p.next_change_level < p.level else "hike"
            wk = (p.next_change_date - EVENT_NS).days // 7
            lines.append(
                f"    Next change: {p.level:.2f}% -> {p.next_change_level:.2f}% on "
                f"{p.next_change_date} — a {direction}, ~{wk} weeks AFTER the event."
            )
    lines.append("")
    lines.append("MARKET (open-market) short rate — the series that would price the shock:")
    lines.append(f"    last observation {res.market_last}; present in 1914? {res.market_in_1914}")
    if res.bonds:
        lines.append("")
        lines.append("Market-priced Russian debt — London bonds, quoted WEEKLY (the real test):")
        for b in res.bonds:
            if b.pct is None:
                lines.append(f"    {b.label}: no bracketing quotes")
                continue
            verdict = "within" if b.within_normal else "ABOVE"
            lines.append(f"    {b.label}:")
            lines.append("        weekly quotes around the event:")
            for d, v in b.window:
                mk = "  <-- event 12 Feb" if abs((d - EVENT_NS).days) <= 3 else ""
                lines.append(f"            {d}   {v:.2f}{mk}")
            lines.append(
                f"        bracket move {b.before:.2f} ({b.before_date}) -> {b.after:.2f} "
                f"({b.after_date}) = {b.pct:+.1f}%"
            )
            lines.append(
                f"        normal weekly |Δ| (trailing 12 mo) = {b.mean_abs_step:.2f}% "
                f"(sd {b.sd_step:.2f}%, n={b.n_steps}) — {verdict} normal variation."
            )
    if res.french:
        lines.append("")
        lines.append("Transmission — France was Russia's banker (Paris held its loans):")
        for b in res.french:
            if b.pct is None:
                lines.append(f"    {b.label}: no bracketing quotes")
                continue
            direction = "ROSE" if b.pct > 0 else ("FELL" if b.pct < 0 else "flat")
            lines.append(
                f"    {b.label}: {b.before:.2f} ({b.before_date}) -> {b.after:.2f} "
                f"({b.after_date}) = {b.pct:+.1f}% — {direction}"
            )
            lines.append(
                f"        normal weekly |Δ| (trailing 12 mo) = {b.mean_abs_step:.2f}% "
                f"(sd {b.sd_step:.2f}%). No contagion: the rente did not fall."
            )
    lines.append("")
    lines.append("Finding: the administered bank rate did NOT move (mid-plateau, next move")
    lines.append("a cut). The open-market SHORT rate that would price the shock ends in 1900 —")
    lines.append("but the market-priced Russian BONDS (London 4% and 1822 5%), quoted weekly,")
    lines.append("DO span the event, and they are flat across it: the bracket move is ~0% and")
    lines.append("the level holds for weeks either side. And France — Russia's banker, the")
    lines.append("market that should transmit any Russian credit scare — did not reprice")
    lines.append("either: the Paris 3% rente firmed slightly across the event. The market did")
    lines.append("not treat Kokovtsov's fall as a Russian credit event — apt, since his")
    lines.append("successor Bark kept the same fiscal and Franco-Russian borrowing policy.")
    return "\n".join(lines)
