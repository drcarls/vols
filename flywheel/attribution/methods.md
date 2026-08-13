# Attribution methods

Lift is the whole game: a decision that *correlates* with a good outcome is
worthless; a decision that *caused* it is the product. The capture schema
supports three ways to isolate causal lift, ordered by how much you can trust
them. One `method` field per outcome says which counterfactual is authoritative,
and every downstream estimate carries a **validity tier** so an experiment and a
guess are never pooled as equals.

| Method | Counterfactual | Required fields | Validity tier | Weight |
|---|---|---|---|---|
| `holdout` | A randomized control arm | `control_value` (+ `n_*`, `variance_*` for a CI) | experimental | 1.00 |
| `pre_post` | The pre-period, optionally difference-in-differences | `baseline_value` (+ optional `comparison_delta`) | quasi | 0.60 |
| `observational` | A modeled match / synthetic control | `counterfactual_value` (computed upstream) | observational | 0.30 |

## How lift is computed (`fct_attribution`)

For every outcome, the model differences the treated value against the
counterfactual the method selects:

```
counterfactual = holdout       -> control_value
                 pre_post       -> baseline_value + coalesce(comparison_delta, 0)
                 observational  -> counterfactual_value

lift_absolute  = treated_value - counterfactual
lift_relative  = lift_absolute / abs(counterfactual)
```

When the outcome carried sample sizes and variances, a normal-approximation
confidence interval is attached (`mean_diff ± 1.96 · sqrt(varₜ/nₜ + var_c/n_c)`).
A lift is `is_significant_positive` only when the CI clears zero. All of this is
plain SQL, so it runs on any warehouse; the harder math (matching, synthetic
control) happens upstream and lands as `counterfactual_value`.

## The rules that keep it honest

1. **Never pool tiers flat.** `mart_mapping_performance` weights lift by
   `validity_weight`, so one clean holdout outvotes a pile of observational
   guesses. Averaging them equally is how you talk yourself into a bad map.
2. **No interval, less trust.** An estimate with no CI (missing `n`/variance)
   is discounted (`× 0.7`) — present but never treated as proven.
3. **Fast + wrong is negative value.** In a commercial decision a confident
   wrong answer costs more than a slow one. The validity tier is what stops the
   flywheel from learning the wrong lesson quickly.
4. **Prefer the ladder.** Push customers up the ladder over time: start
   observational to have *something* from day one, add pre/post as history
   accrues, and graduate the high-stakes decisions to holdouts. The schema lets a
   single mapping family carry all three as evidence matures.

## Why this is the defensible layer

`fct_attribution` → `mart_mapping_performance` is the arrow from raw outcomes to
*"which mapping worked, for which segment."* That table is what sharpens the map,
and its cross-customer form (`mart_benchmark`) is the network effect. A platform
can compute lift; it does not have your permissioned, segment-conditioned record
of which mappings earned it. Own the loop and the map becomes empirically true —
not just plausible.
