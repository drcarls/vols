{{ config(materialized='table') }}

-- One row per surfaced decision, joined to the customer's response and the
-- mapping version that produced it. This is the backbone the flywheel turns on:
-- decision -> action -> (later) outcome, all tied to the map that made it.

with decisions as (
    select * from {{ ref('stg_decisions') }}
),
actions as (
    select * from {{ ref('stg_actions') }}
),
mapping as (
    select * from {{ ref('stg_mapping_versions') }}
)

select
    d.decision_id,
    d.tenant_id,
    d.surfaced_at,
    d.decision_type,
    d.entity_type,
    d.entity_id,
    d.segment_key,
    d.model_confidence,

    -- mapping lineage (the moat link + what this version was sharpened from)
    d.mapping_version_id,
    m.mapping_family,
    m.version              as mapping_version,
    m.parent_version_id    as mapping_parent_id,

    -- response
    a.action_id,
    coalesce(a.response, 'no_action')            as response,
    a.responded_at,
    a.applied_at,
    a.experiment_id,
    a.experiment_arm,
    (a.experiment_id is not null)                as is_experiment,
    (coalesce(a.response,'no_action') in ('accepted','modified')) as was_applied
from decisions d
left join actions a on a.decision_id = d.decision_id
left join mapping m on m.mapping_version_id = d.mapping_version_id
