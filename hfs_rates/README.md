# hfs_rates

**Weekly** pre-1914 money-market rates from **Historical Financial Statistics**
(Center for Financial Stability), spread over London, as the tidy long
`(date, series, value)` CSV that [`crisis_lag`](../crisis_lag) consumes.

This is the finer-than-monthly leg the test needed: [`fred_nber`](../fred_nber)
gives monthly sovereign-bond spreads; `hfs_rates` gives **weekly** money-market
(open-market / private-discount) spreads. It also reaches the powers monthly NBER
could not — Austria for the Balkan Wars, and Germany for Agadir — with the
*correct* fiscally-binding series.

```
HFS Interest_rates.xlsb ─▶ weekly open-market rate ─▶ spread over London (bp) ─▶ tidy long CSV
  client.py                    parse.py                    spreads.py
```

## Coverage

`Market rates--daily` carries **weekly** observations (~756, 1900–1914) for the
European centres:

| series | HFS column | coverage |
|---|---|---|
| `benchmark` | London 90-day bank bills (bid) | weekly 1900–1914 |
| `france` | Paris open-market rate | weekly 1900–1914 |
| `germany` | Berlin open-market rate | weekly 1900–1914 |
| `austria_hungary` | Vienna open-market rate | weekly 1900–1914 |
| `russia` | St Petersburg open-market rate | **sparse — ends 1900** |

Russia's market rate stops in 1900, so its pre-war crises still need another
source; everything else is genuinely weekly.

## ⚠️ Seasonality — why the value is a *spread*, not a level

Money-market rates carry strong **autumn seasonality** (quarter-end/harvest
tightening), and `crisis_lag`'s baseline is the pre-onset *spring* months — so a
raw rate *level* would read seasonal tightening as "crisis." Concretely, Berlin's
raw rate climbed 2.25→4.75% into September 1911 (Agadir), which looks dramatic —
but in the **calm** year 1910 the Berlin−London spread rose to **+2.00** by
October, while in the Agadir year 1911 it was only **+0.12…+0.50**. The autumn
rise was mostly seasonal, not Agadir.

So the emitted `value` is the spread of each power's open-market rate **over
London** (which also tightens in autumn), in basis points — differencing out the
common seasonal/global component. Residual seasonality remains; read the weekly
verdict alongside `fred_nber`'s bond spreads and a control-year comparison.

## The weekly run

`data/crisis_lag_verdict*.txt` (regenerate with `hfs-rates pull` + `crisis-lag`).
With crises mapped to the powers HFS covers weekly
(`events.money_market.yaml`): Morocco 1905 / France, Agadir 1911 / Germany,
Balkans 1912–13 / Austria — the onset→peak-stress lags are **15.1, 20.0 and 32.6
weeks**. Read carefully:

- **No falsification.** The pre-registered floor is 2 weeks; the *fastest*
  money-market peak was ~15 weeks. Nothing became material in days, so the weekly
  data does not support "the brake could have bitten inside a 5-day window."
- **Verdict INCONCLUSIVE** only because the lags *overshoot* the 6–10 week band
  (they are longer, 15–33 wk), not shorter — partly the residual seasonality above.
- **Contrast holds.** Every comparator lag is weeks-to-months; July 1914's
  decision window was ~5 days.

## Usage

```bash
cd hfs_rates && pip install -e .            # needs pyxlsb

hfs-rates plan                              # the column plan, no network
hfs-rates pull --out weekly_long.csv        # download HFS workbook + build
crisis-lag run weekly_long.csv --events events.money_market.yaml
```

## Data & attribution

Source: **Historical Financial Statistics**, ed. Kurt Schuler, Center for
Financial Stability — <https://www.centerforfinancialstability.org/hfs.php>.
HFS restricts database redistribution, so the **raw workbook is not committed**
here (it is `.gitignore`d and downloaded on demand), and neither is the full
derived weekly series; only the small derived `crisis_lag` verdicts are checked
in. Cite HFS per its Data Notes if you use the data.

## Tests

```bash
python -m pytest -q      # 9 tests, no network, no workbook
```
