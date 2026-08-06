# imm_yale

Pull sovereign-bond yields from the Yale ICF **Investor's Monthly Manual** (IMM)
digitisation and emit the tidy long `(date, series, value)` spread CSV that
[`crisis_lag`](../crisis_lag) consumes.

```
IMM search form ─▶ £-s-d yield table ─▶ spread over UK Consols (bp) ─▶ tidy long CSV
   client.py            parse.py             spread.py                   series.py
```

The output is the monthly cross-crisis leg of the falsification test: one spread
series per fiscally-binding power (`france`, `germany`, `russia`,
`austria_hungary`), keyed to the crises in `crisis_lag.events`.

## ⚠️ Status: the live IMM query backend returned no data

This package was built against the real IMM search form and its **request layer
is verified** — the server accepts the POSTs and runs the query (HTTP 200). But
during development **every** query — by security id, by partial name, by exact
name, across all date ranges and every variable group, with a valid session
cookie and `Referer` — came back either `There are no records matching your
selection(s)` or an empty body, and the record RPC (`rpc_retdata.php`) returned
HTTP 500. The 1,330 securities are still listed in the form; the MySQL backend
behind `…/immdatadownload-mysql/` was not serving rows. See **[RECON.md](RECON.md)**
for the full evidence and interface map.

So no real spread series has been produced yet. What ships here is a tested
instrument: the pure logic (£-s-d conversion, spread construction, tidy emit,
catalogue) is fully unit-tested; the response-table parser is written against the
documented column labels and exercised by a synthetic fixture, ready to lock onto
a real response the moment the backend serves one.

**Two ways to complete the pull when unblocked:**
1. Re-run `imm-yale pull` from a network/time where the backend serves rows.
2. Request the full database from Yale (the download page directs you to
   `leigh.clark@yale.edu`) and point `parse`/`series` at the flat file — the
   spread and tidy logic are source-agnostic.

## Usage

```bash
cd imm_yale && pip install -e .

imm-yale plan                                   # print the query plan, no network
imm-yale pull --start 1904 --end 1914 --out spreads_long.csv
imm-yale pull --catalogue securities.yaml --out spreads_long.csv

# then feed the falsification test:
crisis-lag run spreads_long.csv
```

`pull` exits non-zero and says so when the backend yields no rows, so it never
writes a silently-empty CSV that would make `crisis-lag` look "run".

## The securities catalogue — PROVISIONAL

`config.py` (overridable via `securities.example.yaml`) maps each power's series
id to the sovereign issue whose yield carries its spread, over a UK-Consol
benchmark. **These issues are provisional** and are exactly the "which power's
spread carries each crisis" specification to reconcile against the thesis
dataset — the same reconciliation `crisis_lag` flags for its event dates. Prefer
a numeric `security_id` (from the IMM finder) over a name search once known.

| series | provisional issue | benchmark |
|---|---|---|
| france | French 3% Rente | UK Consols 2.5% |
| germany | German 3% Imperial Loan | UK Consols 2.5% |
| russia | Russian 4% Government Loan | UK Consols 2.5% |
| austria_hungary | Austrian 4% Gold Rente | UK Consols 2.5% |

## Why yields, not prices

The IMM records the yield on investment at the late price directly, in £-s-d per
cent (the `Var7` group). Reading the yield avoids reconstructing it from price +
coupon + redemption terms — the error-prone path `crisis_lag`'s README warns
about (coupon dates, ex-coupon drops). The spread then strips the common
interest-rate level, leaving the country-specific risk premium.

## Tests

```bash
python -m pytest -q      # 39 tests, no network
```
