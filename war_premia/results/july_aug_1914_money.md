# The money market through July–August 1914 (descriptive)

The Neal-Weidenmeier short-rate series ends **1914-06-27**. This fills the gap the
paper's data left — the five/six weeks the war actually broke over — from the
**Commercial and Financial Chronicle** (weekly; public domain), recovered from the
FRASER archive via the Wayback Machine. It is **descriptive, not identified**:
too few observations, and the markets closed, so no Rigobon-Sack premium is
possible (see `july1914.py`). Every figure in `data/july_aug_1914_money.csv`
carries the OCR source quote it was read from.

## What the weeks show

**London 3-month bank bills** (the paper's basis asset), Lombard Street:

| week ending | 3-mo bills | note |
|---|---|---|
| 1914-07-04 | ~1.94% | calm |
| 1914-07-11 | **2⅜%** | "This is an advance" |
| 1914-07-18 | ~2.28% | |
| 1914-07-25 | ~2.34% | Paris 2½% |
| 1914-08-01 | — | **market froze** (LSE closed 31 July) |

**Bank of England rate** — the headline:

| date | rate |
|---|---|
| through July | 3% |
| 30 July | 4% |
| 1 Aug | **8%** |
| 3 Aug | **10%** (peak) |
| 6 Aug | 6% |

New York call money covered **2→7%** in the outbreak week (Stock Exchange closed
Friday).

## The finding

Two things, and they reinforce the bond-market reading:

1. **No anticipation.** Through the whole of July the London money market was calm
   — three-month bills drift from ~1.9% to ~2.4%, an ordinary summer firming. The
   market gave no sign of pricing a European war until the very last week. This is
   Ferguson again, in the short rates: the markets were caught off guard.
2. **Then a convulsion — and then the data goes dark.** When war came, the Bank of
   England rate went **3 → 4 → 8 → 10%** in a week and call money to 7%. The bond
   market was routing in the same days — the London French rente fell ~4.4% in the
   final trading week — but then the exchanges closed, and the bond quotes that
   survive are nominal, not trades (an earlier ~2% "cross-section" here was an
   artifact of an ex-dividend baseline and those stale quotes, and is withdrawn —
   see `july1914.py`). The shock hit **liquidity** violently and instantly; the
   priced *war premium* is simply unobservable, because the market shut
   mid-repricing.

So the extension does not add a fifth war-premium estimate — it shows why one
cannot exist for 1914. What is visible before the data goes dark is a market
beginning to rout (money rates and the French rente both), not a placid one.

## Sources

Commercial and Financial Chronicle, vol. 99, weekly issues 4 July – 8 August 1914,
`fraser.stlouisfed.org/files/docs/publications/cfc/cfc_1914MMDD.pdf` (public
domain; recovered via the Internet Archive Wayback Machine). Cite FRASER /
Federal Reserve Bank of St. Louis.
