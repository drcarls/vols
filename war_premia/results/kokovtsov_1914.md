# The Kokovtsov event test — a test the 2005 paper could not run

**Question.** Did Russian markets move around the dismissal of **Vladimir
Kokovtsov** — finance minister 1904–1914 and premier, architect of Russian
fiscal orthodoxy and of the foreign borrowing that anchored Russian credit in
Paris? He was dismissed by imperial rescript of 30 January 1914 (Old Style); his
cabinet formally ended **12 February 1914 (New Style)**. If any Russian asset
should carry a political-risk signal, it is the market losing the man who
guaranteed the debt.

The 2005 paper reported the Russian *rate* as unavailable. The recovered
Neal-Weidenmier data lets the event be run two ways:

```bash
war-premia kokovtsov
```

## Two instruments, one answer: no reaction

### 1. The administered short rate — silent by construction

The only Russian short rate present in 1914 is the **State Bank discount (bank)
rate**. It did **not move**: it sat at 5.50% for a **73-week plateau** (2 Nov
1912 → 28 Mar 1914) that straddles the dismissal, and its *next* change was a
**cut** to 5.00% on 4 Apr 1914 — seven weeks later, opposite sign to stress. It
is an administered policy rate; the Russian State Bank held it flat through the
event, as it held it through the crises where the Reichsbank moved
(`war-premia russia`: St Petersburg bank-rate premium ≈ 0 vs Berlin 0.21). The
**open-market** short rate that would price the shock is exactly the series NW
loses after 1900 (ends 20 Oct 1900), and there is no ruble exchange column in
NW's exchange-rate file.

### 2. Market-priced Russian debt — quoted weekly, and flat across the event

But the long-term bond file **does** supply a market-priced Russian series — the
**Russian New 4% and Russian 1822 5%, quoted weekly in London** — and it spans
the dismissal cleanly. Both are flat across it:

| Russian New 4% (London) | | Russian 1822 5% (London) | |
|---|---|---|---|
| 1914-01-16 | 87.50 | 1914-01-16 | 124.00 |
| 1914-01-23 | 88.75 | 1914-01-23 | 125.00 |
| 1914-01-30 | 89.00 | 1914-01-30 | 125.00 |
| **1914-02-13** (event) | **89.00** | **1914-02-13** (event) | **125.00** |
| 1914-02-20 | 89.00 | 1914-02-20 | 125.00 |
| 1914-02-27 | 89.00 | 1914-02-27 | 125.00 |

- **Bracket move across 12 Feb: +0.0%** on both bonds. The Russian New 4% held
  **89.00 for four straight weeks** (30 Jan – 27 Feb); the 1822 held **125.00**.
  If anything the 4% *firmed* into the dismissal (87.50 → 89.00 in the preceding
  fortnight), then held.
- Against normal weekly variation of **0.59%** (New 4%, sd 0.78%) and **0.13%**
  (1822, sd 0.32%) over the trailing 12 months, a 0.0% move is squarely normal.
- Both ease only modestly by mid-March (New 4% → 88.5, 1822 → 123) — a small,
  general drift weeks after the event, not a reaction to it.

## What it means

At **weekly** resolution — fine enough to isolate a mid-February event — the
market-priced Russian bonds show **no repricing** at Kokovtsov's fall. The market
did not treat the loss of the finance minister as a Russian credit event. That is
historically apt: his successor, Pyotr Bark, continued the same fiscal line and
the Franco-Russian borrowing relationship held; the dismissal was a court
manoeuvre (Kokovtsov had clashed with the Rasputin circle and over the liquor
monopoly), not a change in Russia's willingness or ability to pay.

So the event is real, datable, and — with the recovered data — **runnable on a
genuine market-priced instrument**, which the 2005 paper lacked. The answer is a
clean null on both instruments: the administered rate *cannot* react, and the
market-priced bonds *did not*. The one thing still missing for a Russia-specific
(rather than London-global) read is a St Petersburg open-market discount rate or
a ruble exchange quote for 1913–14 — carried weekly in *The Economist*'s
"Foreign Bourses" column, which is paywalled and was not retrievable here. But
the London Russian bonds already answer the question at the resolution that
matters: no move.

## Reproducibility

`war-premia kokovtsov` prints all of the above from the mirrored data;
`tests/test_kokovtsov.py` asserts the bank-rate plateau, the missing market rate,
and the weekly-bond flatness against the real columns.

## Sources

- Event date: Kokovtsov's cabinet ended 12 Feb 1914 (N.S.); rescript 30 Jan 1914
  (O.S.). See V. N. Kokovtsov, *Out of My Past* (memoirs); standard chronologies.
- Data: Neal-Weidenmier Gold Standard Database — St Petersburg bank/market rates
  (`stinterestrates.xls`) and Russian London bond prices (`longtermbonds.xls`,
  RAW sheet), decoded by `neal_weidenmier.load` / `war_premia.kokovtsov`.
