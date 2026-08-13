{{ config(materialized='view') }}

-- The lineage of the map. Every decision points at exactly one mapping_version;
-- each version knows the family it belongs to and the version it was sharpened
-- from (parent_version_id). That lineage is what lets you say "v4 beat v3 in the
-- mid-market segment" and promote it.

with src as (
    select * from {{ source('flywheel_raw', 'raw_mapping_versions') }}
)

select
    mapping_version_id,
    mapping_family,
    version,
    parent_version_id,
    cast(created_at as {{ dbt.type_timestamp() }})   as created_at,
    cast(retired_at as {{ dbt.type_timestamp() }})   as retired_at,
    definition,                                      -- opaque JSON: rules / params / prompt
    author,
    notes
from src
