# neal_weidenmier

A **mirror** of the Neal-Weidenmeier Gold Standard Database (weekly 1870–1914
interest rates, exchange rates and long-term bond yields, from *The Economist* and
the *Commercial and Financial Chronicle*), plus a loader that decodes its dates
correctly. This is the primary source behind Carls (2005), *"Did Politicians Cry
'War' to Financial Markets Once Too Often?"* — and the HFS money-market series
this repo used earlier is itself derived from it.

## Why this is here (provenance)

The database was published on a mid-2000s Tripod page
(`ebutts05.tripod.com/nealweidenmiergsd/`). **That live site is no longer
reachable** (HTTP-only, host gone). These files were recovered from the **Internet
Archive Wayback Machine** (snapshot 2004-08-21) and are mirrored here so the data
survives. The workbooks are authored by **Larry Neal** and saved by **Marc
Weidenmier** — the originals, not a re-keying.

```
data/stinterestrates.xls   short-term rates, 17 cities   weekly 1870-01-01 .. 1914-06-27
data/exchangerates.xls     exchange rates                weekly .. 1914-06-27
data/longtermbonds.xls     long-term bond yields         weekly .. 1914-10-07
```

## ⚠️ The date trap (read before using)

Excel cannot store positive serial dates before 1900, so the workbook stores dates
in **three segments**:

| rows (true dates) | how stored | reads as |
|---|---|---|
| 1870-01 → 1912-06 | **+100 years** | 1970 → 2012 |
| 1912-07 → 1913-12 | **true** | 1912 → 1913 |
| 1914-01 → 1914-06 | **+100 years** | 2014 |

Read naively, the series looks like it runs to 2014. `load.true_date()` undoes it
(raw year ≥ 1970 ⇒ subtract 100), giving a continuous weekly index. **Anyone
loading these files without this correction will get garbage dates** — hence the
loader.

## Coverage vs the paper — the key point for the extension

The paper analysed short-term rates to **June 1913** (Balkan Wars). The data here
runs a full year further, to **1914-06-27 — the eve of Sarajevo (28 June 1914)**.
So there is an extra year the paper never coded, **but the short-term series ends
just before the July-1914 war weeks** (ultimatum 23 July; London SE closed 31
July). July 1914 is therefore *not* directly available in the short-term rates.
The **long-term bond** file, however, reaches **1914-10-07** and does span the
crisis — the natural instrument for the July-1914 question.

Bonus: the short-term sheet includes a **St. Petersburg (Russia)** column, which
the paper reported as unavailable.

## Usage

```python
from neal_weidenmier.load import load_short_rates, to_series_map, span

obs = load_short_rates("neal_weidenmier/data/stinterestrates.xls")
span(obs)                       # (1870-01-01, 1914-06-27)
smap = to_series_map(obs)       # {"london_trade3mo": [(date, value), ...], "berlin_openmkt": ...}
```

35 tidy series (`<city>_<bank|openmkt|trade3mo>`) for London, Paris, Berlin,
Vienna, Genoa, Amsterdam, Brussels, Madrid, Lisbon, Petersburg, Copenhagen, New
York, Bombay, Melbourne, Geneva, Stockholm, Christiana. `london_trade3mo` is the
paper's basis asset.

## Data & attribution

Neal, Larry and Marc D. Weidenmier, "Crises in the Global Economy from Tulips to
Today: Contagion and Consequences," in *Globalization in Historical Perspective*
(NBER). The authors invite academic use and ask only that this paper be cited.
Mirrored here on that basis; cite Neal & Weidenmier if you use the data.

## Tests

```bash
python -m pytest -q      # date decode (pure) + a read of the mirrored file
```
