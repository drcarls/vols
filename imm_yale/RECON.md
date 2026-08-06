# IMM interface reconnaissance

Reverse-engineering notes for the Yale ICF *Investor's Monthly Manual* (IMM)
download interface, and the state of its backend when `imm_yale` was written.
Everything below was observed directly against the live site.

## Endpoints

| URL | role |
|---|---|
| `…/immdatadownload-mysql/immsrchintstocksall.php` | the search **form** (GET); sets `PHPSESSID` |
| `…/immdatadownload-mysql/alldatadispstocksall.php` | the **data** endpoint the form POSTs to |
| `…/immdatadownload-mysql/findcomdispall.php?tname=StocksFinal` | the name→id **finder** popup (JS/RPC) |
| `…/immdatadownload-mysql/rpc_retdata.php` | record-by-id **RPC** (`reqid`, `tname`) |
| `/imm/downloads.php` | "downloads" page — no self-serve files; directs to `leigh.clark@yale.edu` |

The form's table is `StocksFinal` (the `tname`). It is the only table exposed by
this page; sibling `immsrch*all.php` names probed (intbonds, forgovt, foreign,
govt, bonds, railways, banks, …) all 404.

## Request contract (verified: server accepts and runs these)

POST `alldatadispstocksall.php`, `application/x-www-form-urlencoded`:

- `stype` selects the mode:
  - `byid` + `securityID[]` (repeatable, ≤5) — numeric ids.
  - `comname` + **`cname`** — *partial* company name. **Gotcha:** the HTML input
    is `name=pcname`, but the backend reads the value from `cname`. Confirmed by
    probing every candidate field name — only `cname` was read (others returned
    "Please type a company name").
  - `cname` + `ecname` — *exact* company name.
- `StMon`/`StYear` … `EndMon`/`EndYear` — inclusive date range.
- `VarN[]` checkbox groups select returned columns. The full variable inventory:
  - Var1 `IssuePrice, LastLoanIssuePrice, OriginalIssue`
  - Var2 `EarliestFinalYearLoanRedeem`
  - Var3 `SinkingFund*`
  - Var4 `LastLoanIssuePrice, PriceMonthOpen/High/Low/Late, LastBusiness, PriceMonthLastDay`
  - Var5 `ListPriceJune30, ListPriceJuly30, ListPricesOfficialMin, ListPriceLatestNom`
  - Var6 `Dvd*` (dividend)
  - **Var7 `YieldInvtLatePricePound / …Shilling / …Pence`** ← the £-s-d yield used here
  - Var8 `YearPriceHigh, YearPriceLow`
  - Var9 `AmntSubscribedOrOutstanding, AmntLoanUnredeemed, PresentAmntQuotedInLondon, Par, Paid`
- `format` — output rendering.

The form's `securityID[]` `<select>` is pre-populated with **1,330** numeric ids,
**10001–11330** (values only, no names).

## Backend state at time of writing: not serving rows

Every attempt to retrieve data returned no rows:

| query | result |
|---|---|
| `byid` 10001/10002/10100/10500/10700/11300/11330, windows 1869–1929 | `no records` (142 B) or empty body (0 B) |
| `byid` with static fields (IssuePrice, Par) 1900–1914 | `no records` / empty |
| `comname`+`cname` = Russia, Russian, French, Germ, Austr, Consol, Japan, Italian, Brazil | `no records matching your selection(s)` |
| `cname`+`ecname` = Russia | `did not return any results` |
| all of the above **with** a prior GET (valid `PHPSESSID`) + `Referer` | unchanged |
| `rpc_retdata.php` `reqid=10001..` | **HTTP 500** |

Two distinct empty responses were seen and are handled in `parse.py`:
`There are no records matching your selection(s)` (a 142-byte page) and a
**0-byte body** (a server-side error path, seen on some pre-1890 and mid-range-id
queries). Combined with the RPC 500s, this reads as a backend/database outage
(the path is literally `immdatadownload-mysql`), not a client-side mistake — the
request layer is accepted and processed, there is simply nothing behind it.

## Things that do *not* work headlessly here

- **The finder** (`findcomdispall.php`) renders matches via IE-era JS
  (`opener.document.all.sid`, XMLHttpRequest to `rpc_retdata.php`); the POST
  response is just an empty `displaytable` skeleton, so name→id mapping needs a
  browser or the RPC (which 500s).
- **A headless browser** can't traverse this environment's egress proxy —
  Chromium resets on every navigation (even `example.com`), because the proxy
  only tunnels CONNECT and the browser's connection is reset; `curl`/`urllib`
  through `HTTPS_PROXY` work fine. So the client here is `urllib`-based, not
  browser-driven.

## Completing the pull later

1. Re-run `imm-yale pull` when the backend serves rows; drop one populated
   response into `tests/fixtures/` to lock the column mapping (see `parse.py` —
   columns are matched by header text, so it should adapt without code changes).
2. Or obtain the full database by email and point `parse`/`series` at the flat
   file; the spread/tidy logic is source-agnostic.
3. Reconcile `securities.example.yaml` (which issue per power) and the
   `crisis_lag` event dates against the thesis dataset before trusting a verdict.
