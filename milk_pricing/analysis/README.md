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
| `pa_minimum_pricing.py` | `reports/pa_minimum_pricing.md` — whether PA's minimum retail milk price is racially disparate, and the national burden-vs-price decomposition |
| `walmart_basket_national.py` | `reports/walmart_basket_national.md` — Walmart cross-store dispersion by product: fluid milk takes 17-19 prices, everything else 1-2 |
| `dairy_pattern.py` | `reports/dairy_pattern.md` — the three-tier dairy pattern in the existing Aldi SC panel: fluid milk store-managed, other dairy one statewide price |
| `basket_test.py` | `docs/basket_spec.md` — comparison-basket test: is milk uniquely variable among Great Value items, and the within-store placebo. Run `--selftest` to verify the code path. |
| `within_metro.py` | `reports/within_metro_test.md` — compares high- and low-Black stores sharing a metro (Atlanta and 8 others), the design with no between-region confound |
| `sc_variation.py` | `reports/why_sc_varies.md` — why SC has large within-state variation: rules out artifact, Class I, and zone boundary; identifies the metro discount |
| `zone_override.py` | `reports/zone_vs_override.md` — splits price into the centrally-set zone component and the local override component, tests each for a racial gradient, and restates Louisiana as block assignment |
| `pricing_unit.py` | `reports/walmart_pricing_geography.md` §3–4 — recovers the geographic unit at which Walmart sets milk prices, and re-tests Finding B under four region definitions |
