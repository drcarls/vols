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
| `pricing_unit.py` | `reports/walmart_pricing_geography.md` §3–4 — recovers the geographic unit at which Walmart sets milk prices, and re-tests Finding B under four region definitions |
