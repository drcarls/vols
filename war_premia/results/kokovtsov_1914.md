# The Kokovtsov event test — a test the 2005 paper could not run

**Question (proposed as a falsification-style probe).** Did Russian short rates
move around the dismissal of **Vladimir Kokovtsov** — finance minister 1904–1914
and premier, the architect of Russian fiscal orthodoxy and of the foreign
borrowing that anchored Russian credit in Paris? He was dismissed by imperial
rescript in late January 1914 (Old Style); his cabinet formally ended **12
February 1914 (New Style)**. If any Russian rate should carry a political-risk
signal, it is the market losing the man who guaranteed the debt.

The 2005 paper reported the Russian rate as unavailable. The **recovered
Neal-Weidenmier data adds a St Petersburg column**, so the event is now runnable:

```bash
war-premia kokovtsov
```

## The result — a clean, informative null

```
Weekly BANK (State Bank discount) rate straddling the event:
    1914-02-07   5.50%
    1914-02-14   5.50%
    1914-02-21   5.50%
  Plateau: 5.50% unbroken 1912-11-02 → 1914-03-28 (73 weeks, straddling the event)
  Next change: 5.50% → 5.00% on 1914-04-04 — a cut, ~7 weeks AFTER the event.
MARKET (open-market) rate: last observation 1900-10-20; present in 1914? False
```

- The one Russian short rate present in 1914 is the **State Bank discount (bank)
  rate — an administered policy rate.** Around Kokovtsov's fall it **did not
  move.** It sat at 5.50% for a **73-week plateau** running from the Balkan-war
  hike of 2 Nov 1912 straight through to 28 Mar 1914 — the dismissal falls in the
  middle of it. The *next* change was a **cut** to 5.00% on 4 Apr 1914: seven
  weeks later, and the **opposite sign** to stress. No reaction.
- The rate that could actually price the shock — the **St Petersburg
  open-market rate** — is exactly the series NW loses after 1900. It ends **20
  Oct 1900**, with no 1914 observation. NW's exchange-rate file carries no
  St Petersburg/ruble column either, so there is *no* market-priced Russian
  short series to test in 1914.

## What it means

The event is real, datable, and runnable — and the run tells you the **data
cannot see it.** The administered bank rate is silent by construction: the
Russian State Bank held it flat through a first-order political shock, exactly as
it held it through the crises where the Reichsbank moved (`war-premia russia`:
St Petersburg bank-rate premium ≈ 0 vs Berlin 0.21). The series that would carry
a Kokovtsov signal — an open-market rate — is the one the database lacks after
1900.

So this does not overturn or confirm a war-risk reading; it **sharpens the
paper's general "Russia unavailable" caveat into a specific, dated
demonstration**: even at the sharpest available Russian political event, the only
Russian short rate we have moves to nothing. A genuine test of Russian
political-risk pricing needs the open-market St Petersburg rate (or a ruble
exchange series), which neither the paper nor this recovered dataset supplies.

## Sources

- Event date: Kokovtsov's cabinet formally ended 12 Feb 1914 (N.S.); dismissal
  rescript late Jan 1914 (O.S.). See V. N. Kokovtsov, *Out of My Past* (memoirs);
  standard cabinet chronologies.
- Rate data: Neal-Weidenmier Gold Standard Database, St Petersburg bank and
  market rates (`../../neal_weidenmier/data/stinterestrates.xls`), decoded by
  `neal_weidenmier.load`.
