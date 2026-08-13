{{ config(materialized='view') }}

-- Typed, cleaned decisions. The segment object is hashed into a stable
-- segment_key so lift can be grouped "for which customer type" without
-- exploding the JSON in every downstream model (warehouse-agnostic: the
-- segment payload stays opaque; only its hash is used as a grouping key).

with src as (
    select * from {{ source('flywheel_raw', 'raw_decisions') }}
)

select
    decision_id,
    tenant_id,
    cast(surfaced_at as {{ dbt.type_timestamp() }})            as surfaced_at,
    decision_type,
    entity_type,
    entity_id,
    mapping_version_id,
    cast(model_confidence as {{ dbt.type_float() }})           as model_confidence,
    segment_key,                       -- stable hash of the segment attributes, computed at ingestion
    recommendation,                    -- opaque JSON, passed through
    context                            -- opaque JSON, passed through
from src
