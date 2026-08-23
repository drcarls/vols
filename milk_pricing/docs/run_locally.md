# Running the basket test on your own machine

The basket file never has to leave your laptop. The analysis is one script with one
dependency.

```bash
git clone -b claude/walmart-milk-pricing-sc-m7zc99 https://github.com/drcarls/vols
cd vols/milk_pricing
pip install numpy

# 1. see what your basket file contains and how it classifies
python3 analysis/basket_test.py ~/path/to/basket.csv \
    --describe --meta ~/path/to/national_walmart_milk_by_store_zip.csv

# 2. run it, assigning any columns --describe flagged UNCLASSIFIED
python3 analysis/basket_test.py ~/path/to/basket.csv \
    --meta ~/path/to/national_walmart_milk_by_store_zip.csv \
    --milk gv_milk_gal --kvi gv_eggs_dz,gv_bread --pantry gv_flour5,gv_beans,gv_oil
```

`--meta` points at the milk file you already have — the export named
`national_walmart_milk_by_store_zip.csv`, or any CSV with `zip`, `state`, `county`,
`pct_black`, `median_income`, `population` (header matched case-insensitively; `geo` and
`whole_milk` used if present). `--describe` needs nothing else and prints, per item column:
coverage, mean, sd, CV, and a suggested KVI/pantry classification.

Paste the output back and I will read it.

Sanity check that the environment is right, before touching your data:

```bash
python3 analysis/basket_test.py --selftest
```

That builds a synthetic basket with a known answer — pantry flat, milk carrying an injected
%Black gradient — and should end with the placebo recovering it at roughly t +5 under state
fixed effects. If that runs, the real file will run.

## Or just upload it

Attaching the CSV to the conversation puts it where I can read it directly, and I will run
everything and write it up. Either path works; the local one keeps the file on your machine.
