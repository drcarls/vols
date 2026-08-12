# presales_scout

A pre-sales prospecting engine for **Cyber Defencely**. Point it at a set of
Swedish companies and it ranks them by how good a prospect they are — built
around the pitch that lands right now: the Swedish Cybersecurity Act
(*Cybersäkerhetslagen*, SFS 2025:1506, in force since **15 Jan 2026**) put a
large set of companies into NIS2 scope, and many of them are not ready.

It answers, per company:

1. **Are they in NIS2 scope?** — from SNI industry code + size (≥50 employees
   or ≥€10M turnover/balance sheet; some digital-infra always in scope).
2. **Is their email security weak?** — public SPF/DMARC DNS check.
3. **Do they have a visible CISO?** — via the **Bright Data SERP API**. A
   company with no publicly visible security leader is a direct
   CISO-as-a-Service opening.

…then scores and ranks them, so a consultant gets *"the 30 transport/energy
firms in scope, with weak email security and no visible CISO,"* highest-fit
first.

## Install

```bash
cd presales_scout
python3 -m pip install -e .        # or: pip install -r requirements.txt
```

## Run (offline, no token needed)

The tool ships with fixtures so the whole pipeline runs with no Bright Data
account and no network:

```bash
presales --offline discover --input fixtures/candidates.sample.csv --out ranked.csv --top 10
presales --offline scan --name "Nordfrakt Logistik AB" --sni 49410 --employees 180
```

(`--offline` forces the fixture CISO backend; drop `--no-email` to run the
live DNS check when the network is available.)

## Run (live CISO detection via Bright Data SERP)

Set your token in the environment — **never commit it**:

```bash
export BRIGHTDATA_API_TOKEN="…"     # from your Bright Data account
presales discover --input my_candidates.csv --out ranked.csv
```

With a token present (and without `--offline`) the CISO backend switches to
the live Bright Data SERP API automatically. It runs one Google query per
company:

```
site:linkedin.com/in ("CISO" OR "Head of Information Security"
  OR "informationssäkerhetschef" OR "säkerhetschef" …) "<Company>"
```

and reads the LinkedIn hits. Cost is ~$1.50 / 1000 requests (one request per
company; 5k/month free tier), and failed requests aren't billed.

## Input format (Stage 1)

Candidates come from a CSV — see `fixtures/candidates.sample.csv`:

| column | meaning |
|---|---|
| `name` | company legal name (required) |
| `domain` | for the email-security check |
| `org_number` | Swedish organisationsnummer |
| `sni_code` | SNI industry code — drives the NIS2 sector match |
| `employees`, `turnover_eur`, `balance_sheet_eur` | drive the NIS2 size test |

In v1 you supply this CSV. A live **allabolag / Bolagsverket** backend that
builds the candidate universe by SNI + size (so you don't hand-assemble the
list) is the planned next step — it populates the same `Company` shape, so
nothing downstream changes.

## How it's organized

```
src/presales_scout/
  models.py                 # Company, Nis2Verdict, EmailSecuritySignal, CisoSignal, ProspectReport
  collectors/
    nis2.py                 # SNI + size -> NIS2 scope verdict
    email_security.py       # SPF/DMARC DNS check (pure grader is unit-tested)
    ciso/
      base.py               # CisoBackend protocol + normalized SerpResult
      query.py              # query building, title classification (EN + SV), parsing
      brightdata_serp.py    # live Bright Data SERP backend + parse_serp_json()
      fixture.py            # offline backend from saved JSON
      detector.py           # results -> scored CisoSignal
  scoring.py                # combine signals -> fit score + brief
  pipeline.py               # CSV -> analyze each -> rank -> CSV
  cli.py                    # `presales scan` / `presales discover`
```

Swap or add a CISO backend by implementing `CisoBackend.search()` — e.g. a
`BrightDataLinkedInBackend` using the LinkedIn Scraper API for a richer
org-chart view.

## Important caveats

- **CISO absence is a confidence signal, not proof.** No search hit can mean a
  private profile, a Swedish-only title, or a tiny firm. `none_found` results
  always carry `verify_recommended` — eyeball before outreach.
- **Stay passive.** Everything here reads public DNS and public search
  results. No port scanning or vuln probing — that needs the prospect's
  authorization.
- **GDPR.** CISO detection pulls *named individuals*. For B2B prospecting a
  legitimate-interest basis is defensible, but keep the data minimal, document
  the basis, and set a retention limit. Don't hoard profiles.
- The NIS2 check is a **screening heuristic**, not a legal determination.

## Tests

```bash
python3 -m pytest -q
```
