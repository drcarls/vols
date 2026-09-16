# Reproduction scripts

Standalone analysis scripts backing the reports in `reports/`. Run from the
`milk_pricing/` package root (they resolve `data/...` relative to the cwd):

```
cd milk_pricing && python3 analysis/metros.py
```

The `data/` directory is gitignored — regenerate it with the collectors in
`src/milk_pricing/sources/` before running these.

| Script | Backs |
|---|---|
| `metros.py` | `reports/tx_ca_metros.md` §2 — TX/CA metro regressions inside Aldi's verified footprint |
| `ca_sens.py` | `reports/tx_ca_metros.md` §2 — leave-out, leave-one-county-out, within-county permutation for the CA %Black cell |
| `txca_memo.py` | `reports/tx_ca_metros.md` §3 — the memo's matched-pair design on TX/CA race and ethnicity tails |
| `hisp_fe.py` | `reports/tx_ca_metros.md` §3 — within/between-county decomposition of the Hispanic gap |
| `fb_within.py` | `reports/tx_ca_metros.md` §4 — same decomposition applied to the Finding B states |
| `sc_basket.py` | `reports/brightdata_zipcode_trap.md` §7 — the 13-item Great Value basket across all 92 SC stores; `--build` converts the raw snapshot |
| `bd_zipcode_probe.py` | `reports/brightdata_zipcode_trap.md` — why Bright Data's Walmart zipcodes template pins the store but returns a national online price; §7 has the full 92-store SC pull |
| `within_state_zones.py` | `reports/cover_memo_rev2.md` — re-estimates the memo's within-state racial gradients with SEs clustered on the differential zone, the level at which the differential actually varies |
| `walmart_collect.py` | per-store Walmart milk via a Bright Data Scraping Browser zone — WRITTEN BUT NEVER RUN; preflight exits unless a JS-executing zone exists, and volume collection is gated behind a passing `--verify` against three known SC shelf prices |
| `aldi_2026_09.py` | `reports/aldi_2026_09.md` — the September re-collection: proves the shop is the pricing unit (641 shops, 0% multi-price), reproduces the milk carve-out (47 distinct prices vs 3 for cottage cheese), and shows the retailer comparison is unstable (+22c → +16c → +3c) |
| `aldi_collect.py` | re-collects the Aldi panel recording zip, zone, **shop** and the full dairy basket; resumable, direct to aldi.us with no proxy or credential |
| `aldi_comparison.py` | `reports/aldi_comparison.md` — Aldi as a control retailer on the same 1,333 matched ZIPs: Walmart +14c in high-Black low-income rural ZIPs, Aldi −11c, difference +24c (t +0.96 clustered); Aldi's zones are racially flat by construction |
| `within_state_design.py` | `reports/within_state_design.md` — redoes the comparison inside each state with within-state income and racial cuts, after national quartiles and absolute thresholds were found to select on state; reverses the rural gradient to −12c |
| `segmented_rural.py` | `reports/segmented_rural.md` — the client's own stratified design: the retail gradient is real in low-income rural cells (+19c, +8.5c within state) and absent or reversed in urban ones, which is why the pooled estimate reads null |
| `ca_wic.py` | `reports/ca_wic.md` — audits the memo's California WIC section against CDPH's actual participant counts by county and race; every figure reproduces |
| `above_cost_regional.py` | `reports/above_cost_regional.md` — the above-freight markup by region: +3.92c/gal in the South, −6.58c in the West, and no racial gradient inside any region |
| `usdss.py` | `reports/usdss.md` — tests the "it's geography" defence against USDA's own cost model (Exhibit MIG-16A, 3,085 counties): the transport surface is itself racially graded, and by more than the pre-2025 differentials |
| `counterfactual_schedules.py` | `reports/counterfactual.md` addendum — racial incidence of all four county-level schedules that were before USDA, including MIG's filed alternative |
| `counterfactual.py` | `reports/counterfactual.md` — verifies the 3.81c-to-5.59c widening on 3,100 counties and quantifies revenue-neutral alternatives |
| `reia_audit.py` | `reports/reia_audit.md` — USDA's own economic analysis: the \$4.01bn transfer it quantified, why it declined to model impacts, and the absence of any consumer analysis |
| `docket_audit.py` | `reports/docket_audit.md` — who commented on AMS-DA-23-0031, whether consumer incidence was raised, and the *Block* obstacle |
| `cria_audit.py` | `reports/cria_audit.md` — first independent audit of the 2025 FMMO final rule and its Civil Rights Impact Analysis, against the 131-page 1999-2000 comparator |
| `clean_panel.py` | `reports/clean_panel.md` — every headline number re-run on the panel with statutorily-regulated and non-contiguous states excluded, shown raw vs clean |
| `state_pricing_laws.py` | `reports/state_pricing_laws.md` — three regimes of state pricing law, which compress prices and which do not, and which comparator states are contaminated |
| `pa_minimum_pricing.py` | `reports/pa_minimum_pricing.md` — whether PA's minimum retail milk price is racially disparate, and the national burden-vs-price decomposition |
| `walmart_basket_national.py` | `reports/walmart_basket_national.md` — Walmart cross-store dispersion by product: fluid milk takes 17-19 prices, everything else 1-2 |
| `dairy_pattern.py` | `reports/dairy_pattern.md` — the three-tier dairy pattern in the existing Aldi SC panel: fluid milk store-managed, other dairy one statewide price |
| `basket_test.py` | `docs/basket_spec.md` — comparison-basket test: is milk uniquely variable among Great Value items, and the within-store placebo. Run `--selftest` to verify the code path. |
| `within_metro.py` | `reports/within_metro_test.md` — compares high- and low-Black stores sharing a metro (Atlanta and 8 others), the design with no between-region confound |
| `sc_variation.py` | `reports/why_sc_varies.md` — why SC has large within-state variation: rules out artifact, Class I, and zone boundary; identifies the metro discount |
| `zone_override.py` | `reports/zone_vs_override.md` — splits price into the centrally-set zone component and the local override component, tests each for a racial gradient, and restates Louisiana as block assignment |
| `pricing_unit.py` | `reports/walmart_pricing_geography.md` §3–4 — recovers the geographic unit at which Walmart sets milk prices, and re-tests Finding B under four region definitions |
