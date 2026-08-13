{{ config(materialized='view') }}

-- Measured outcomes with their counterfactual basis. Nothing method-specific
-- is computed here -- staging just types the fields; fct_attribution turns the
-- right counterfactual into lift based on `method`.

with src as (
    select * from {{ source('flywheel_raw', 'raw_outcomes') }}
)

select
    outcome_id,
    decision_id,
    tenant_id,
    metric,
    cast(window_start as {{ dbt.type_timestamp() }})       as window_start,
    cast(window_end   as {{ dbt.type_timestamp() }})       as window_end,
    method,                                                -- holdout | pre_post | observational
    cast(observed_value      as {{ dbt.type_float() }})    as observed_value,
    cast(control_value       as {{ dbt.type_float() }})    as control_value,
    cast(baseline_value      as {{ dbt.type_float() }})    as baseline_value,
    cast(comparison_delta    as {{ dbt.type_float() }})    as comparison_delta,
    cast(counterfactual_value as {{ dbt.type_float() }})   as counterfactual_value,
    n_treatment,
    n_control,
    cast(variance_treatment as {{ dbt.type_float() }})     as variance_treatment,
    cast(variance_control   as {{ dbt.type_float() }})     as variance_control
from src
