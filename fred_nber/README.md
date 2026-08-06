# fred_nber

Pull pre-1914 sovereign-bond yields from **FRED** (the NBER Macrohistory
database mirror) with **no API key**, take the spread over the England-Consol
benchmark, and emit the tidy long `(date, series, value)` CSV that
[`crisis_lag`](../crisis_lag) consumes.

```
FRED keyless CSV ─▶ monthly yield ─▶ spread over England Consols (bp) ─▶ tidy long CSV
   client.py                            spreads.py                        spreads.py
```

This is the **first data path that runs end-to-end** for the falsification test.
Unlike [`imm_yale`](../imm_yale) — whose Yale backend was down — FRED serves the
data openly:

```
https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES_ID>
```

## What it covers (and what it can't)

Real NBER Macrohistory (Chapter 13, Interest Rates) series, verified to span the
pre-war window:

| series | FRED id | source series | coverage |
|---|---|---|---|
| `benchmark` | `M1341CGB40000M156NNBR` | England Yield of Consols | 1888-03 … 1938-12 |
| `france` | `M13027FRM156NNBR` | France Security Yields | 1898-01 … 1939-07 |
| `germany` | `M1328ADEM193NNBR` | Germany Bond Yields | 1870-01 … 1913-12 |

**Russia and Austria-Hungary are not available here.** NBER Macrohistory carries
their *discount rates*, not sovereign *bond yields*. That gap is exactly why the
thesis reached for the Investor's Monthly Manual — so `fred_nber` (France,
Germany) and `imm_yale` (the rest) are complementary, both emitting the same CSV
schema to stack under `crisis_lag`.

## Usage

```bash
cd fred_nber && pip install -e .

fred-nber plan                                  # list the series, no network
fred-nber pull --out spreads_long.csv           # keyless fetch -> tidy CSV
crisis-lag run spreads_long.csv                 # the falsification test
```

The client tries the system `curl` first (reliable through TLS-reintercepting
proxies) and falls back to `urllib`; both honour the environment's proxy/CA.

## The first real run

`data/fred_spreads_long.csv` is the committed output (749 monthly rows, 1888–1938;
regenerate any time with `fred-nber pull`). Running the thesis's **default**
events on it (`data/crisis_lag_verdict.txt`):

```
Agadir_1911   germany   1911-07-01   ok   peak 1911-11-01   lag 17.6 wk
VERDICT: INCONCLUSIVE  (1 comparator; the Russia/Austria crises are no_data)
```

Only Agadir maps to a covered power, so one comparator is measured — a real
result, honestly thin. The German spread's peak stress lands ~17.6 weeks after
the Agadir onset (outside the predicted 6–10 week band at monthly resolution).

### Caveat on the France/Germany example spec

`events.fr_de.example.yaml` narrows the crises to the covered powers (same thesis
onset dates) and yields three comparators — but treat it as an **illustration of
the instrument's limits, not a historical verdict**. It reports `FALSIFIED`
solely because Morocco-1905/France "peaks" at 0.1 weeks — and that peak is a
**3 bp wobble** (123 vs a ~116 bp baseline) sitting on the first post-onset
monthly point, against an unusually quiet baseline. It is monthly-resolution
noise, not stress that became material in days. This is precisely why the real
test needs (a) the correct fiscally-binding series per crisis (Russia/Austria via
IMM) and (b) finer resolution in the crisis weeks (the weekly *Chronicle* / daily
*Le Temps*). Read it as a worked example of *why those are needed*.

## Tests

```bash
python -m pytest -q      # 10 tests, no network
```
