{{ config(materialized='table') }}

-- THE MOAT, PER CUSTOMER.
-- "Which mappings actually drove results, for which customer type." Grain:
-- (tenant, mapping_family, mapping_version, segment_key, metric). This is the
-- table the map is sharpened from -- rank versions within a segment, promote
-- the winners, retire the losers. Every closed loop adds evidence here.
--
-- Lift is weighted by validity so an experimental read outvotes an
-- observational guess instead of being averaged flat with it.

with a as (
    select * from {{ ref('fct_attribution') }}
    where lift_relative is not null
)

select
    tenant_id,
    mapping_family,
    mapping_version_id,
    mapping_version,
    segment_key,
    metric,

    count(*)                                             as n_outcomes,
    sum(case when validity_tier = 'experimental' then 1 else 0 end) as n_experimental,

    -- validity-weighted mean relative lift (the headline "does this map work here")
    sum(lift_relative * validity_weight) / nullif(sum(validity_weight), 0) as weighted_mean_lift,
    avg(lift_relative)                                   as simple_mean_lift,
    {{ flywheel_percentile('lift_relative', 0.5) }}     as median_lift,

    -- share of loops where the lift was positive and significant
    avg(cast(is_significant_positive as {{ dbt.type_float() }})) as win_rate,
    avg(validity_weight)                                as avg_validity,
    max(window_end)                                     as last_outcome_at
from a
group by 1,2,3,4,5,6
