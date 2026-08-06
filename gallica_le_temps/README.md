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

# Run the whole pipeline; writes a CSV of crop URLs (and OCR values with --ocr)
gallica-le-temps run config.example.yaml --output le_temps_1914.csv
gallica-le-temps run config.example.yaml --ocr

# Debug: build a IIIF crop URL from raw pixel coords
gallica-le-temps crop-url bpt6k239abcd 3 1200 400 240 80
```

The output CSV has one row per (date, target) with `status`, `ark`,
`ocr_quality`, the IIIF `region`, the `crop_url` (so a human can eyeball every
figure), and — with `--ocr` — the read `value`. `status` is one of `ok`,
`no_issue`, `low_quality`, `not_found`, or `no_value`, so gaps are explicit
rather than silent.

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
python -m pytest -q      # 56 tests, no network required
```

## Network note

Extraction requires outbound access to `gallica.bnf.fr`. If your environment's
egress policy blocks it (as some sandboxed/CI environments do), the pure logic
and the full test suite still run; the live steps will surface the network error
rather than fabricating data. Run `search`/`run` from a network where Gallica is
reachable.
