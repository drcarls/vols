# Comparison basket — collection spec

What to pull, from which stores, and in what format, so `analysis/basket_test.py` runs
against it directly.

## Stores

**The same store list as `national_walmart_official.csv`** — all 4,149, or a subset. If
subsetting, the two highest-value cuts are:

1. **Atlanta MSA (71 stores)** — 30 stores ≥30% Black and 13 ≤10% in one market. This is where
   the within-store placebo is cleanest, since geography is already controlled
   (`reports/within_metro_test.md`).
2. **South Carolina (92 stores)** — spans the full $2.32–$4.00 milk range, so it directly tests
   whether the metro discount is milk-specific.

~160 stores across those two covers both questions. The full 4,149 is better if it is cheap.

## Items

| Column name | Item | Why |
|---|---|---|
| `whole_milk` | GV Whole Vitamin D Milk, gallon (SKU 10450114) | re-pull alongside, so both series share an instrument |
| `eggs_12ct` | GV Large White Eggs, 12 ct | traffic driver |
| `white_bread` | GV White Sandwich Bread, 20 oz | traffic driver |
| `bananas` | Bananas, per lb | classic traffic driver, not GV |
| `flour_5lb` | GV All-Purpose Flour, 5 lb | pantry control |
| `green_beans_can` | GV Cut Green Beans, 14.5 oz | pantry control |
| `veg_oil_48oz` | GV Vegetable Oil, 48 oz | pantry control |
| `ketchup_20oz` | GV Tomato Ketchup, 20 oz | pantry control |
| `paper_towels` | GV Paper Towels | pantry control, non-food |

The script keys off these exact column names (`KVI` and `PANTRY` sets at the top). Any subset
works; a minimum useful pull is `whole_milk` plus **two** pantry items.

## Format

**Column names do not need to match.** Run `--describe` first and the script reports every item
column with its coverage, mean, sd and CV, plus a suggested KVI/pantry classification; anything
it cannot place is flagged UNCLASSIFIED. Then classify explicitly:

```
python3 analysis/basket_test.py data/walmart_basket.csv --describe
python3 analysis/basket_test.py data/walmart_basket.csv \
    --milk gv_milk_gal --kvi gv_eggs_dz,gv_bread --pantry gv_flour5,gv_beans,gv_oil
```

Either layout. Only `zip` and the prices are required — state, county, geo and demographics are
joined from the milk file. Demographic and ID columns from the existing milk file
(`pct_black`, `median_income`, `store_address`, …) are ignored automatically if present, so an
extended version of `national_walmart_milk_by_store_zip.csv` with extra product columns works
as-is.

**Long** (one row per store × item):
```
zip,item,price
29020,whole_milk,3.82
29020,flour_5lb,2.48
```

**Wide** (one column per item):
```
zip,store_id,whole_milk,eggs_12ct,flour_5lb,green_beans_can
29020,634,3.82,3.12,2.48,0.98
```

Save to `data/walmart_basket.csv`, then:
```
python3 analysis/basket_test.py data/walmart_basket.csv
```

## Collection conditions that matter

1. **Same method as the milk file.** A dispersion comparison is only valid if both series come
   from one instrument. A basket pulled a different way confounds exactly what is being measured.
2. **Same window.** Pull all items in one pass per store. A rollback that starts mid-collection
   shows up as cross-sectional dispersion.
3. **Keep the SKU guard.** `src/milk_pricing/sources/walmart_page.py` rejects a page whose
   primary `usItemId` is not the SKU requested — this is what caught Walmart substituting a
   national marketplace offer ($9.97 in four states) for a store shelf price. Every basket item
   needs the same guard; pantry staples have more third-party listings than milk, not fewer.
4. **Record misses as blank, not zero.** An out-of-stock or non-carried item must be empty.

## What the run produces

1. Dispersion by item — CV, IQR, distinct price count, and the traffic-driver / pantry ratio.
2. Within-state dispersion, which strips the coarse geographic component.
3. Urban-minus-rural gap per item — does the metro discount exist only on milk?
4. %Black gradient per item, rural.
5. **The within-store placebo**: log(milk) − mean log(pantry) at the same store, regressed on
   %Black. This differences out cost, freight, format, competition and trade-area demographics,
   because they hit both products at that store equally.

The pipeline is tested end to end against a synthetic fixture with a known answer:
`python3 analysis/basket_test.py --selftest`.

## If the pull already exists

A basket pulled earlier will work without re-collection, as long as it carries a ZIP (or a
store_id that maps to one) and per-item prices. Two caveats worth checking before trusting the
comparison:

- **Was it pulled in the same window as the milk file?** If the basket is materially older,
  the dispersion comparison is still valid (each item's cross-sectional spread is measured
  within its own pull), but the *within-store placebo* in §5 assumes milk and pantry prices
  come from the same store visit. If they do not, re-pull milk alongside — that is why
  `whole_milk` is on the item list.
- **More stores than the milk file is fine.** The join is by ZIP and drops non-matches; extra
  stores simply widen the per-item dispersion tables without affecting the demographics-linked
  tests.

## Note on this environment

The collection cannot originate here: `walmart.com` returns `HTTP 307 blocked` through the
session proxy, and no `BRIGHTDATA_API_TOKEN` is set. Setting that variable (as an env var, not
pasted into chat) makes `walmart_page.py` usable, but it resolves the store from the proxy exit
location rather than a pinned store — the defect found earlier in this project, where 5 of 7
sampled ZIPs came back as the proxy's ZIP rather than the store's. Reusing the method that
produced the milk file avoids that and is the reason to prefer it.
