# cow_mid

**Objective** crisis onset dates and hostility levels for
[`crisis_lag`](../crisis_lag), from the **Correlates of War Militarized
Interstate Dispute (MID v5)** data — the war-events dataset founded at Michigan
and mirrored at ICPSR.

`crisis_lag`'s event onsets were **hand-coded**, which is the single biggest
credibility gap in a lag test: if you pick the onset, you can move the lag. This
package replaces the guesswork with COW's externally-coded dispute **onset date**
and **1–5 hostility level** (1 none · 2 threat · 3 display of force · 4 use of
force · 5 war).

```
COW MID v5 zip ─▶ join MIDA+MIDB ─▶ map each crisis to its dispute ─▶ crisis_lag events YAML
   client.py          parse.py               crises.py                    cli.py
```

## What the objective coding shows

`cow-mid show` against MID v5:

| crisis | MID | objective onset | hostility | series | vs hand-coded |
|---|---|---|---|---|---|
| Morocco 1905 | — | *none* | — | france | **no great-power MID** |
| Bosnia 1908 | 30 | 1908-10-06 | use of force | russia | matches |
| Agadir 1911 | 315 | 1911-07-01 | display of force | germany | matches |
| Balkans 1912–13 | 21 | **1912-11-21** | display of force | austria_hungary | **+6 wk later** |
| July 1914 | 257 | 1914-07-23 | war | austria_hungary | matches |

Three onsets **validate** the hand-coding exactly. Two honest results fall out:

- **Morocco 1905 has no great-power MID** — it never crossed COW's
  militarization threshold, so it gets no objective onset and is omitted rather
  than mapped to a wrong dispute.
- **The Balkans/Austria onset is objectively 1912-11-21** (Austria's mobilisation
  crisis vs Russia+Serbia), six weeks *later* than the First Balkan War's opening
  that the hand-coding used. On the weekly `hfs_rates` data this shortens the
  measured lag from **32.6 → 26.3 weeks** — the hand-coded onset was too early and
  inflated the lag. That is exactly the bias objective onsets remove.

One mismatch is recorded, not hidden: for **Bosnia 1908** the binding power
(Russia) is *not* a militarized participant in MID 30 (Serbia vs Austria-Hungary)
— Russia backed down below the threshold.

## Usage

```bash
cd cow_mid && pip install -e .

cow-mid show                              # list the mapped disputes + gaps
cow-mid events --out events.mid.yaml      # emit the crisis_lag event spec

# run either data leg on objective onsets:
crisis-lag run ../fred_nber/data/fred_spreads_long.csv --events events.mid.yaml
crisis-lag run ../hfs_rates/data/weekly_spreads_long.csv --events events.mid.yaml
```

`events.mid.yaml` (the emitted spec) and the two `verdict_*_mid.txt` runs are
checked in. COW MID is a discrete war-*event* dataset — it objectifies the
**onset**, not a continuous war-probability path; the `series` (which power's
spread carries each crisis) remains the thesis's choice, constrained here to a
plausible actor and documented per crisis in `crises.py`.

## Data & attribution

Source: **Correlates of War, Militarized Interstate Disputes v5.0** —
Palmer et al.; <https://correlatesofwar.org/data-sets/MIDs/>. Downloaded openly
from COW (same data as ICPSR study 24386, no login). The raw MID files are **not
vendored** (downloaded on demand); only the tiny derived event spec is committed.
Cite COW MID if you use it.

## Tests

```bash
python -m pytest -q      # no network, no data files
```
