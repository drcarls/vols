# Bonds or commercial paper? Which instrument carries the brake

The lag and cause-or-cover tests were first run on **long bonds**. But bonds and
commercial paper measure different things, and the difference matters for *this*
mechanism:

- **Long bonds price solvency** — can the state ultimately pay? A slow,
  forward-looking default-risk signal.
- **Commercial paper / money-market rates** (open-market bills, discount, call
  money) **price the immediate cost of raising cash** — can the state and its
  banks fund a mobilization *this month*?

The book's financial **brake** is a **mobilization-finance** mechanism: armies are
mobilized on short-term borrowing (Treasury bills, central-bank advances,
discounting), so the constraint bites first and sharpest in the **money market**.
July 1914 is the proof — the seizure was in commercial paper (Bank of England
3→4→8→10% in a week; NY call money to 7%) while bonds merely slid. And Carls's own
war-risk premia were estimated on the money-market city rates. So for the brake,
**commercial paper is the more appropriate instrument** — bonds were a convenient
but slow proxy.

Both are now built from NW (`build_nw_money.py`: city open-market rate minus the
London 3-mo trade bill; Amsterdam open-market as the neutral). Running the same
tests on each:

## Cause-or-cover — commercial paper sees the stress *faster*

Percentile of the crisis-window rise (power − neutral) vs the non-crisis null:

| crisis (power) | bonds 90/180/270 | **commercial paper** 90/180/270 |
|---|---|---|
| **Balkans (Austria)** | 0 / 0 / 89 | **92 / 84 / 77** |
| **Agadir (Germany)** | 49 / 93 / 90 | **67 / 51 / 40** |
| **Bosnia (Russia)** | 68 / 85 / 78 | 0 / 81 / 72 *(admin. bank rate)* |
| **Morocco (France)** | 17 / 13 / 9 | 0 / 0 / 42 |

- **Austria flips from slow to fast.** On bonds its stress arrives only at the
  270-day horizon (89th); on **commercial paper it is at the 92nd percentile
  within 90 days** (~13 weeks). The mobilization-cost signal is prompt; the bond
  solvency signal lagged it by months.
- **Germany is acute-then-resolved.** Its money market spikes early (67th at 90d)
  and fades as the crisis settles — the sharp September-1911 Berlin panic — where
  the bond signal built more slowly. Two instruments, two true stories: a fast
  liquidity scare and a slower solvency drift.
- **France stays weak** on both — the creditor power, no mobilization crunch.
- **Russia can't be assessed cleanly:** NW has no St Petersburg *open-market*
  rate, only the administered bank rate (sticky — see the Kokovtsov analysis), so
  the money-market "russia" is a policy rate, not a market one.

## Lag — peaks are similar, but that's the point

Onset→peak lags (seasonal, to strip the autumn money-market tightening):

| crisis | bond peak | money-market peak |
|---|---|---|
| Morocco | 16 wk | 18 wk |
| Bosnia | 16 wk | 4.6 wk *(admin. rate)* |
| Agadir | 17 wk | 20 wk |
| Balkans | 37 wk | 33 wk |

The *peaks* are similar because the pre-war crises were **resolved before
mobilization** — so the money market only tightened gradually, never seized. The
one acute money-market brake (July 1914, actual mobilization) is exactly the
observation the short-rate data stops before (27 June 1914). So commercial paper
is the instrument that *would* show the brake biting hard — but in the comparators
it shows the mild version (they were braked early), and in 1914 it is censored.

## So: bonds or commercial paper?

**Commercial paper, for the brake and the lag** — it is the instrument the
mechanism actually runs through, it carries the stress faster (Austria within ~13
weeks, moving the timing toward the book's 6–10 wk that the bond peaks overstated
as 37), and it is what the paper used. **Bonds, for the war-risk premium / solvency
question** — the slower, default-risk read, useful precisely because it is *not*
the liquidity scare. Report both; do not read a bond peak lag as the transmission
speed of a money-market brake. Caveats: money rates are strongly seasonal (use
`--seasonal`), Russia has no open-market series, and the acute 1914 case is
censored.

## Reproduce

```bash
cd crisis_lag
python build_nw_money.py ../neal_weidenmier/data/stinterestrates.xls
crisis-lag run data/mm_spreads_long.csv --seasonal      # money-market lag
python cause_or_cover.py                                  # bonds (edit to point at mm_yields for CP)
```
