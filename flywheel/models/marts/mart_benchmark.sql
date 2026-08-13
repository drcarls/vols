{{ config(materialized='table') }}

-- THE NETWORK EFFECT, SAFELY.
-- Cross-customer rollup of how each mapping family performs by segment. This is
-- the asset no single customer and no platform can reproduce -- and the thing
-- you give back as "the benchmark" in exchange for the data rights to build it.
--
-- Privacy is structural, not a promise: a row is emitted ONLY when at least
-- `benchmark_k` distinct tenants contribute (k-anonymity), and no tenant id or
-- tenant-level value ever appears. Grain: (mapping_family, segment_key, metric).

{% set k = var('benchmark_k', 5) %}

with perf as (
    -- one contribution per tenant so a heavy user can't dominate the pool
    select
        tenant_id,
        mapping_family,
        segment_key,
        metric,
        weighted_mean_lift,
        win_rate,
        n_outcomes
    from {{ ref('mart_mapping_performance') }}
),

pooled as (
    select
        mapping_family,
        segment_key,
        metric,
        count(distinct tenant_id)                    as tenant_count,
        sum(n_outcomes)                              as n_outcomes_total,
        avg(weighted_mean_lift)                      as benchmark_mean_lift,
        {{ flywheel_percentile('weighted_mean_lift', 0.25) }} as p25_lift,
        {{ flywheel_percentile('weighted_mean_lift', 0.50) }} as median_lift,
        {{ flywheel_percentile('weighted_mean_lift', 0.75) }} as p75_lift,
        avg(win_rate)                                as benchmark_win_rate
    from perf
    group by 1,2,3
)

select *
from pooled
where tenant_count >= {{ k }}      -- k-anonymity gate: never expose a thin cell
