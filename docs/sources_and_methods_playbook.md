# Sources & methods playbook — running any pre-1914 crisis through this rig

A standing reference for reusing what this project built: the archives, the exact pull
commands, and the per-crisis checklist. Everything here is open-access; the one rule
that makes it scale is at the bottom.

## 1. The reusable tools in this repo

| Tool | What it does | Point it at a new crisis |
|---|---|---|
| `war_premia/crisis_deviation.py` | Each city's money rate vs **its own seasonal baseline** over a window (the NY-control method, generalized) | `--treatment YEAR --baselines Y,Y,Y --window MM-DD:MM-DD --cities slug,slug` |
| `war_premia/spot_to_arrive.py` | Berlin's spot-vs-to-arrive (term) gap; **quarter-end seasonal**, not war-specific | `--year YYYY` for one autumn's trajectory (inputs are Chronicle extractions) |
| `gallica_le_temps/` | date → ark → ALTO OCR / IIIF crop for French titles | change the title ark + date |
| `neal_weidenmier/` | weekly city rates 1870 → 1914-06-27 (`stinterestrates.xls`) | the quantitative backbone |

```bash
# list the available Neal-Weidenmier city slugs
cd war_premia && python crisis_deviation.py --list
# e.g. Algeciras/first-Moroccan crisis, spring 1906:
python crisis_deviation.py --treatment 1906 --baselines 1904,1905,1908 \
    --window 01-01:06-30 --cities paris_openmkt,berlin_openmkt,vienna_openmkt,london_trade3mo
```

## 2. The source map (endpoints, copy-paste)

| Center | Source | Pull |
|---|---|---|
| **London** | *Commercial & Financial Chronicle* (FRASER) | `curl fraser.stlouisfed.org/files/docs/publications/cfc/cfc_YYYYMMDD.pdf` (Saturdays); `pypdf` → the money paragraph sits on the early pages. 17–85 MB each. |
| **Berlin** | Lansburgh, *Die Bank* (Zenodo **5115892**, CC-BY) | one 11 MB zip, plain text under `Artikel/…YEAR…`. Monthly analysis (his articles only — no rate tables). |
| **Vienna** | *Neue Freie Presse* (ANNO) | OCR text: `anno.onb.ac.at/cgi-content/annoshow?text=nfp\|YYYYMMDD\|PAGE` (finance ~p.13–17). Image: `…?call=nfp\|YYYYMMDD\|PAGE\|100.0\|0`. Daily. |
| **Paris** | *Le Temps* (Gallica) | date-redirect `gallica.bnf.fr/ark:/12148/cb34431794k/date YYYYMMDD` → `bpt6k…`; then ALTO: `RequestDigitalElement?O=ark:/12148/ARK&E=ALTO&Deb=5`. *Bulletin financier* on p.5; *Changes* (FX) table there too. `texteBrut` 302-redirects — use ALTO. |
| all | Neal–Weidenmier `stinterestrates.xls` | already local; weekly, ends 1914-06-27. |

Access gotchas we hit: *Der Österreichische Volkswirt* is catalogued on ANNO (`aid=ovw`)
but **image-only/sparse** for 1911–12 — no OCR; its analytical text is on HathiTrust
(catalog 102712766), which is access-restricted here. Raffalovich's *Le Marché financier*
is on Gallica **only for 1896–1901 and 1910** — not the 1911–12 Agadir volume. Gallica and
FRASER both 403 a non-browser User-Agent — send a browser UA.

## 3. The per-crisis checklist (four signals, then triangulate)

For a crisis window, pull these per capital and cross-check them against each other:

1. **Central-bank / private discount rate** — did the bank tighten? (NW + local press.
   e.g. Austro-Hungarian Bank 5→5½→6% across the Balkan escalation.)
2. **Money-market / report rate** — the squeeze. London: Chronicle. Vienna: NFP
   "Ultimo/Privatdiskont". Paris: Le Temps *"loyer de l'argent à la liquidation"*.
3. **Exchange at the gold points** — the capital-flight footprint. Le Temps *Changes*
   table (FF/100 marks; par ≈ 123.46, gold point ≈ 122.8) or NFP "Check auf …". A
   currency pinned to its gold point = money leaving that center.
4. **Press attribution (cause-vs-cover)** — does the finance column *name* the political
   event? (Le Temps: *"les négociations relatives au Maroc"*.)

Then run `crisis_deviation.py` to see whether the move clears the city's own seasonal
noise. Agree across sources before you claim anything.

## 4. Where this reaches (all pullable with the above)

- **First Moroccan / Algeciras 1905–06** — NW + Le Temps + NFP. (The Chronicle did not
  yet print the spot/to-arrive split in 1905, so that one test doesn't apply then.)
- **Bosnian annexation 1908–09** — Lansburgh silent, money easy; but NFP/Le Temps *daily*
  show whether Vienna/Paris twitched.
- **Italo-Turkish / Tripolitania 1911–12** — already surfaces inside the Agadir Le Temps
  bulletins; a clean adjacent case.
- **Second Balkan War, June–July 1913** — extend the NFP Vienna trace.
- **July–August 1914** — Chronicle money + Lansburgh's London-freeze already done; add NFP
  (Vienna → 8%) and Le Temps daily for the closing bourses.
- **Non-war controls** — the 1907 panic, the 1910 stringency (a firm *war-free* autumn):
  same pull, no war, to keep isolating the war component. (1907 is a poor *baseline* —
  exclude it and say so.)

## 5. The discipline that makes it usable

Every figure is **OCR-grade until checked**: locate the number in the text, keep the raw
OCR string in the CSV, and verify against the page image before it enters the manuscript.
Never synthesize a series to fill a gap — a reconstructed anchor-plus-interpolation
dataset returns only the spikes hard-coded into it. That rule is what lets this scale
without fabricating.

## Reproduce examples

```bash
cd war_premia
python crisis_deviation.py --list
python crisis_deviation.py --treatment 1912 --baselines 1909,1910,1913 \
    --window 09-01:12-31 --cities berlin_openmkt,vienna_openmkt,paris_openmkt   # Balkan winter
python spot_to_arrive.py --year 1910                                            # one autumn's gap
```

Worked examples in the same `docs/` folder: `chapter3_digest_for_handoff.md`,
`lansburgh_die_bank_autumn1911.md`, `continental_press_warscares.md`.
