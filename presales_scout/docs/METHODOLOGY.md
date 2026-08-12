# Methodology & Data Sources

*What this engine did, and where every data point came from.*

This is the "show your work" companion to the prospect brief. Everything in the
demo run (12 Aug 2026, 10 companies) is reproducible from public sources. Nothing
was scanned, probed, guessed, or pulled from behind a login. For each signal
below: **what we collect**, **the exact source**, **how automated it is today**,
and **its confidence / limits**. Read the limits — a signal you can't defend in
front of a prospect is worse than no signal.

---

## 1. NIS2 scope — *"are they legally obligated?"*

| | |
|---|---|
| **What** | Is the company an "essential" or "important" entity under Sweden's Cybersäkerhetslagen (SFS 2025:1506, implementing NIS2)? Sector match + size threshold (≥50 staff **or** ≥€10M turnover / balance sheet). |
| **Source** | SNI industry code → NIS2 sector map (`collectors/nis2.py`, hand-curated from the Act's 18 sectors). Size from public company figures. |
| **Automation** | Sector→scope logic is fully automated. In this run the **SNI code and headcount were hand-verified** per company (annual reports, company sites), because we don't yet have a registry feed. |
| **Confidence** | High for the sector match. The size figures are public but manually sourced — this is the one input that doesn't scale without a registry (see §8). |
| **Limit** | A screening heuristic, **not a legal determination**. Entity-wide scope means one qualifying activity pulls the whole company in; we flag, a lawyer confirms. |

## 2. Email security — *the fastest observable gap*

| | |
|---|---|
| **What** | SPF present & not soft-fail, DMARC present & enforced (`p=reject/quarantine`, not `p=none`), plus DNSSEC / CAA / MTA-STS / TLS-RPT as hardening signals. |
| **Source** | **Live public DNS**, queried over DNS-over-HTTPS (`https://dns.google/resolve`) — TXT/MX/DNSKEY/CAA records. `collectors/email_security.py`, `dns_hardening.py`. |
| **Automation** | **Fully automated and live.** No key, no cost. Runs in seconds per domain. |
| **Confidence** | High — these are authoritative published records. A missing DMARC record is a fact, not an inference. |
| **Limit** | Says nothing about inbound filtering or internal mail hygiene — it's the *spoofability of their domain*, which is exactly the quick-win Cyber Defencely leads with. |

## 3. CISO / security leader — *the CISO-as-a-Service opening*

| | |
|---|---|
| **What** | Does a publicly visible security leader exist (CISO / Head of Information Security / *säkerhetschef* / *informationssäkerhetschef*)? And the stronger signal: are they **actively hiring one**? |
| **Source** | Public web + LinkedIn search results. Query builder in `collectors/ciso/query.py` (EN + Swedish titles). Designed for the **Bright Data SERP API** (`brightdata_serp.py`); this run used **live web search** as the backend (no token in sandbox). "Hiring" = a live public job posting. |
| **Automation** | Query + parse + classify is automated. The SERP fetch is pluggable — drop in a Bright Data token and it runs unattended at ~$1.50/1000 companies. |
| **Confidence** | Medium — **absence is a confidence signal, not proof.** A null result can be a private profile, a Swedish-only title, or a title held quietly by a CIO. Every `none_found` carries `verify_recommended`. |
| **Limit** | Names individuals → treat under GDPR legitimate-interest, keep minimal, set retention. The **hiring** signal is the high-confidence one: a live req is public intent + budget. |

## 4. Passive attack surface — *the "other vulnerabilities"*

| | |
|---|---|
| **What** | Web security headers (HSTS, CSP), software-version disclosure / EoL components, `security.txt` (RFC 9116) presence, subdomain footprint & takeover candidates, internet-exposed services / OT. |
| **Source** | HTTP response headers of the public homepage (`web_headers.py`, `security_txt.py`); **Certificate Transparency logs** via `crt.sh` for subdomains (`ct_surface.py`); **Shodan InternetDB** (free per-IP, no key) for exposed services (`shodan_exposure.py`). |
| **Automation** | Fully automated, all free public sources. |
| **Confidence** | High for what's *present* (a disclosed version string is a fact). "Takeover candidate" is a **candidate** — flagged for manual confirmation, never asserted. |
| **Limit** | Read-only observation of already-public data. We never send a probe the target would see as a scan. |

## 5. Supplier map — digital *(NIS2 Art. 21(2)(d))*

| | |
|---|---|
| **What** | Third parties the company depends on that are visible from outside: mail/DNS providers (MX/NS), and third-party code executing in their own website (analytics, chat/AI widgets, ad pixels, tag managers). |
| **Source** | MX/NS records (DoH) + the site's own `content-security-policy` and inline script origins (`supply_chain.py`). A curated known-vendor dictionary labels the origins. |
| **Automation** | Fully automated. |
| **Confidence** | High — these vendors are declared by the company's own headers/markup. |
| **Limit** | Only *externally observable* suppliers. It won't see an internal ERP vendor. 147 digital supplier relationships mapped across the 10. |

## 6. Supplier map — procurement *(the angle no competitor pitches)*

| | |
|---|---|
| **What** | NIS2-critical systems the (mostly municipally-owned) utilities have **outsourced via public tender**: IT services, software, telecom, OT/electrical, control systems. |
| **Source** | **TED — the EU's Tenders Electronic Daily** award records (`api.ted.europa.eu/v3/notices/search`), filtered by buyer, categorised by CPV code (`procurement.py`). Named winners resolved via **openprocurements.com** (`se.openprocurements.com`), which also aggregates national below-threshold portals TED never sees (`openproc_suppliers.py`). |
| **Automation** | Fully automated. 124 procurement supplier relationships + 63 named-supplier links pulled. |
| **Confidence** | High for the *linkage* (award decisions are public record). The per-tender **category** guess from title keywords is deliberately conservative and marked as weak (see limit). |
| **Limit** | Title-keyword categorisation over-matches (e.g. "konsult" flags any consultant). Reliable per-supplier industry classification needs the supplier's own SNI code — same registry dependency as §8. We ship the *verified linkage*, not the noisy guess. |

## 7. Big suppliers as leads — *the second funnel*

| | |
|---|---|
| **What** | The named IT/OT suppliers (Atea, Advania, ABB Power Grids, Ramböll…) ranked by how many public bodies they serve — because each of those buyers now demands NIS2 assurance *from the supplier*. |
| **Source** | Aggregated from the §6 award records: count of distinct public buyers per supplier (`openproc_suppliers.supplier_profile`). Domain resolution is **ownership-verified** (brand must appear as a whole word on a homepage that also resolves) to avoid inventing wrong domains. |
| **Automation** | Fully automated, with a deliberate accuracy gate: unverifiable domains are dropped rather than guessed. |
| **Confidence** | High for reach (counted from records). We **withheld** an earlier noisier scored list until the domain/category accuracy was fixed — the reliable list ships name + verified public-sector reach + utility linkage only. |
| **Limit** | Reach ≠ revenue. It's a proxy for "how much NIS2 pressure is flowing at this supplier," which is the point. |

## 8. Context mapping — finding → framework → service

Every raw finding is enriched into a defensible talking point through a **two-layer**
design so the automation *cannot* fabricate a compliance claim:

1. **Deterministic backbone** (`kb/crosswalk.yaml` + `context_engine.py`): a finding
   is tagged with one control theme; the theme maps — from a curated table — to its
   NIS2 Art. 21(2) measure, ISO 27001:2022 control, base severity, and the Cyber
   Defencely service that closes it. **All framework citations come from this table
   only.** Fully auditable, no invention possible.
2. **Narrative layer** (optional, key-gated): an LLM writes *only* the prose (risk
   sentence, remediation, sales opener), grounded on the evidence, and is **never
   asked for a control ID** — so it can't hallucinate one. Falls back to a
   deterministic template with no API key.

This split is itself a lesson-learned: an earlier free-form categoriser mislabelled
suppliers, so the compliance-bearing fields were moved behind a fixed table.

---

## The one dependency worth naming: a company-registry feed

Everything above is automated and free **except candidate generation** — turning
"all Swedish energy & transport firms ≥50 staff" into a list of names+domains+SNI
codes. In this run that step was hand-verified, which is why the 10 are trustworthy.

That seam is now built: `collectors/registry/` harvests the candidate universe by
SNI code + size through a pluggable backend — live **Roaring** Company Prospecting
API (key-gated), a downloaded **allabolag / Bolagsverket / Roaring** CSV export, or
an offline sample — and re-checks NIS2 scope before anything goes downstream
(`presales harvest --sectors energy,transport --out candidates.csv`). What remains
account-specific is the credential/export itself: plug in Cyber Defencely's registry
access and the 50–100 list generates itself. This is the honest scaling boundary,
and now the code path to cross it.

## What "passive & public" means, precisely

- Public DNS records (SPF/DMARC/DNSSEC/CAA/MX/NS) over DoH.
- Public HTTP response headers and homepage markup of the company's own site.
- Public Certificate Transparency logs (crt.sh).
- Shodan InternetDB (already-indexed, per-IP, free).
- Public EU/Swedish procurement records (TED, openprocurements).
- Public web/LinkedIn search results.

No port scans. No vulnerability probes. No authenticated access. Nothing the target
would observe as directed activity against them. The NIS2 verdict is a screening
heuristic; individual-level CISO data is handled as minimal, retention-limited,
legitimate-interest B2B processing.

## Reproducing the run

```bash
cd presales_scout
python3 -m pip install -e .
presales discover --input candidates.csv --out ranked.csv   # scope + email + CISO
# passive attack-surface, supplier, and procurement collectors run per-domain
python3 -m pytest -q                                         # 23 tests
```

Demo artifacts (10-company run, 12 Aug 2026): account leads, 89 attack-surface
findings, 147 digital suppliers, 124 procurement suppliers, 63 named suppliers.
