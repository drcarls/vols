{{ config(materialized='view') }}

-- The customer's response to each decision, including experiment assignment
-- when a holdout was used. `response` is kept for all four values -- 'modified'
-- and 'rejected' are training signal, not rows to drop.

with src as (
    select * from {{ source('flywheel_raw', 'raw_actions') }}
)

select
    action_id,
    decision_id,
    tenant_id,
    cast(responded_at as {{ dbt.type_timestamp() }})   as responded_at,
    response,
    applied_change,                                    -- opaque JSON
    cast(applied_at as {{ dbt.type_timestamp() }})     as applied_at,
    experiment_id,
    experiment_arm,                                    -- 'treatment' | 'control' | null
    experiment_unit_id
from src
