# gallica-le-temps

Locate-with-text, read-from-image extraction of **French rates and Paris bourse
quotations** from *Le Temps* (1861–1942), via the Gallica / BnF open APIs.

This gives **daily** resolution for crisis weeks — a complement to weekly series
— by pulling the figure straight off the scanned finance page instead of trusting
raw full-text OCR.

## The principle

We never trust the OCR of the number itself. Instead we:

1. **Search** the SRU API (CQL) for the *Le Temps* issue of a given date, and
   filter on the `ocrquality` index (0–100) so only good scans are processed.
2. **Read** the page's ALTO XML — word-level bounding boxes for every OCR'd
   token.
3. **Locate** the target by a reliable *text anchor* (a label such as
   `Banque de France`, or a rente row like `3 0/0`) and take the value token(s)
   that follow it on the same line.
4. **Crop** that region: scale the ALTO coordinates into the IIIF image space and
   build a IIIF Image API URL.
5. **Extract** the value from the cropped image (optional Tesseract OCR), and
   parse period-French number formats.

```
date ─▶ SRU search ─▶ issue ARK ─▶ ALTO (word boxes) ─▶ locate anchor
                                                            │
        value ◀── parse ◀── OCR crop ◀── IIIF crop URL ◀── scale coords
```

## Endpoints used

| Step   | Endpoint |
|--------|----------|
| Search | `https://gallica.bnf.fr/SRU?operation=searchRetrieve&version=1.2&query=…` |
| ALTO   | `https://gallica.bnf.fr/RequestDigitalElement?O=<ark>&E=ALTO&Deb=<page>` |
| IIIF info | `https://gallica.bnf.fr/iiif/ark:/12148/<ark>/f<page>/info.json` |
| IIIF crop | `https://gallica.bnf.fr/iiif/ark:/12148/<ark>/f<page>/<x,y,w,h>/full/0/native.jpg` |

The SRU issue lookup uses the `arkPress` index against the *Le Temps* title
notice (`ark:/12148/cb34431794k`):

```
arkPress all "cb34431794k_date19140728" and ocrquality > "080.00"
```

## Install

```bash
cd gallica_le_temps
pip install -e .            # core (requests, PyYAML)
pip install -e ".[ocr]"    # + Tesseract OCR of crops (needs the tesseract binary)
pip install -e ".[dev]"    # + pytest
```

## Usage

Everything is data-driven — no dates or securities are baked into the package.
Copy `config.example.yaml` and edit the window and targets:

```yaml
date_start: "1914-07-25"
date_end:   "1914-08-05"
min_ocr_quality: 80
targets:
  - name: rente_3pct
    anchors: ["3 0/0", "3 %"]
    page: 3
  - name: banque_de_france
    anchors: ["Banque de France"]
    page: 3
```

```bash
# Find the issue for a date (prints ark + OCR quality)
gallica-le-temps search 1914-07-28 --min-ocr-quality 80

# Run the whole pipeline. --ocr reads the value off each crop (needs Tesseract).
gallica-le-temps run config.example.yaml --ocr --output le_temps_1914.csv

# Debug: build a IIIF crop URL from raw pixel coords
gallica-le-temps crop-url bpt6k239abcd 3 1200 400 240 80
```

## Output formats

`run --format` chooses the CSV shape; the default is the tidy series so the
output is ready to align with other sources.

- **`long`** (default) — one row per `(date, series)` with a `source` column and
  full provenance (`ark`, `page`, `ocr_quality`, `region`, `crop_url`, `status`).
  This is the canonical **join target**: stack this Gallica series with a weekly
  (or any other) first source using a plain concat keyed on `(date, series)`.
  Set the label with `--source` (default `le_temps`).

  ```
  date,series,value,unit,source,status,ark,page,ocr_quality,region,crop_url
  1914-07-28,rente_3pct,84.25,FRF,le_temps,ok,bpt6k…,3,95.4,1200,400,…,https://…
  ```

- **`wide`** — one row per date, one column per series, built on a **complete
  daily date spine** across the config window. Every calendar day is present;
  market-closed / missing days are explicit empty cells, so this is a genuine
  gap-free **daily** series ready to resample or align against a weekly one.

  ```
  date,rente_3pct,banque_de_france,change_londres
  1914-07-27,,,
  1914-07-28,84.25,4100,25.30
  1914-07-29,,,
  ```

- **`raw`** — the underlying one-row-per-(date,target) provenance dump (all
  `ExtractionResult` fields), for debugging.

`status` is one of `ok`, `no_issue`, `low_quality`, `not_found`, or `no_value`,
so gaps are always explicit rather than silent. The `value` column is populated
only when `--ocr` ran; without it, use the long form and read each figure from
its `crop_url`. The Python API mirrors this: `to_long()`, `to_wide()`,
`write_long_csv()`, `write_wide_csv()` in `gallica_le_temps.series`.

## Tuning targets

The finance page layout shifts over the decades, so:

- **`page`** — set per target; use `search` + the IIIF viewer to find the bourse
  page for your window.
- **`anchors`** — list OCR spelling variants; the first that matches wins.
  Matching is case- and accent-insensitive.
- **`max_tokens` / `skip_tokens`** — widen the value run, or skip filler tokens
  between the label and the number.
- **`include_anchor: true`** — widen the crop to include the label, which makes
  the crop self-verifying for a human reviewer.
- **`pad_ratio`** — grow the crop around the value (default 0.15).

## Design notes

- **Every network boundary is behind `GallicaClient`** (`client.py`). The rest of
  the package is pure logic — query building, XML parsing, coordinate math,
  number parsing — and is fully unit-tested against fixtures in `tests/`, with no
  network. The pipeline takes an injected client so tests drive it with canned
  responses.
- **Coordinate scaling.** ALTO coordinates live in the ALTO `<Page>` space, which
  can differ in resolution from the IIIF full image; `scale_region` rescales by
  the ratio of the two dimensions (read from `info.json`) and clamps in-bounds.
- **Politeness.** `GallicaClient` throttles requests and retries transient
  failures with backoff. TLS verification is never disabled.

## Tests

```bash
python -m pytest -q      # 64 tests, no network required
```

## Network note

Extraction requires outbound access to `gallica.bnf.fr`. If your environment's
egress policy blocks it (as some sandboxed/CI environments do), the pure logic
and the full test suite still run; the live steps will surface the network error
rather than fabricating data. Run `search`/`run` from a network where Gallica is
reachable.

## Live Gallica status (verified 2026-08)

Gallica's interface drifted since this package was first written; the client was
updated to match, and the reachable surface here is now:

- **SRU search — works.** Gallica **blocks non-browser User-Agents** (403), so
  the client presents a browser UA. The issue query was also updated: the old
  `arkPress all "…_dateYYYYMMDD"` form now returns 0 records; the current form is
  `arkPress all "cb34431794k_date" and gallicapublication_date="YYYY/MM/DD"`. And
  the issue's own document ARK (`bpt6k…`) now lives in Gallica-namespace fields,
  not `dc:identifier` (which carries the parent *title* ARK) — the parser prefers
  the document ARK. `search <date>` returns the right issue ARK again.
- **IIIF images — work.** `…/iiif/<ark>/fN/info.json` and region crops return 200.
- **OCR text — gated.** `RequestDigitalElement?E=ALTO` resets the connection and
  the `.texteBrut` full text redirects to an **ALTCHA** anti-bot challenge. The
  "locate-with-text" step depends on the ALTO layer, so end-to-end value
  extraction needs either a network/session where ALTO is un-gated, or the
  `--ocr` path (local Tesseract) reading the IIIF crops instead.
- **Transport.** Through a TLS-reintercepting egress proxy `requests` can fail
  the tunnelled handshake; the client falls back to the system `curl`, which
  honours the same proxy/CA. Both paths keep TLS verification on.
