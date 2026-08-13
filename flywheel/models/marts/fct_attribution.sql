{{ config(materialized='table') }}

-- THE HEART OF THE FLYWHEEL.
-- Turns each measured outcome into an isolated lift estimate, using whichever
-- counterfactual the outcome actually carries. One row per (decision, metric):
-- the `method` field selects the counterfactual, and a validity tier records
-- how much to trust it -- an experimental read and an observational guess must
-- never be pooled as equals.
--
-- Warehouse-agnostic: only standard SQL + a normal-approximation confidence
-- interval (mean diff +/- 1.96 * standard error) computed from the sample
-- sizes/variances the outcome carries. Matching/synthetic-control math happens
-- upstream and lands as counterfactual_value; here we only difference and grade.

with o as (
    select * from {{ ref('stg_outcomes') }}
),
spine as (
    select * from {{ ref('fct_decision_spine') }}
),

lift as (
    select
        o.outcome_id,
        o.decision_id,
        o.tenant_id,
        o.metric,
        o.method,
        o.window_start,
        o.window_end,
        o.observed_value                                       as treated_value,

        -- the counterfactual actually in force for this method
        case o.method
            when 'holdout'       then o.control_value
            when 'pre_post'      then o.baseline_value + coalesce(o.comparison_delta, 0)
            when 'observational' then o.counterfactual_value
        end                                                    as counterfactual_value,

        o.n_treatment,
        o.n_control,
        o.variance_treatment,
        o.variance_control
    from o
),

scored as (
    select
        lift.*,
        (treated_value - counterfactual_value)                            as lift_absolute,
        case when counterfactual_value is null or counterfactual_value = 0
             then null
             else (treated_value - counterfactual_value) / abs(counterfactual_value)
        end                                                               as lift_relative,

        -- normal-approx standard error when the outcome carried variances + n
        case
            when variance_treatment is not null and n_treatment > 0
             and variance_control  is not null and n_control  > 0
            then sqrt( (variance_treatment / n_treatment) + (variance_control / n_control) )
        end                                                               as std_error
    from lift
),

graded as (
    select
        scored.*,
        (lift_absolute - 1.96 * std_error)   as ci_low,
        (lift_absolute + 1.96 * std_error)   as ci_high,

        -- trust tier: an experiment is not the same evidence as a guess
        case method
            when 'holdout'       then 'experimental'
            when 'pre_post'      then 'quasi'
            when 'observational' then 'observational'
        end                                  as validity_tier,
        case method
            when 'holdout'       then 1.00
            when 'pre_post'      then 0.60
            when 'observational' then 0.30
        end                                  as validity_base
    from scored
)

select
    g.outcome_id,
    g.decision_id,
    s.tenant_id,
    s.segment_key,
    s.mapping_family,
    s.mapping_version_id,
    s.mapping_version,
    g.metric,
    g.method,
    g.window_start,
    g.window_end,
    g.treated_value,
    g.counterfactual_value,
    g.lift_absolute,
    g.lift_relative,
    g.std_error,
    g.ci_low,
    g.ci_high,
    g.validity_tier,
    -- significant only when we have a CI that clears zero on the right side
    case when g.ci_low is not null and g.ci_low > 0 then 1 else 0 end     as is_significant_positive,
    -- final validity discounts an unmeasurable interval; feeds weighting downstream
    case when g.std_error is null then g.validity_base * 0.7 else g.validity_base end as validity_weight
from graded g
join spine s on s.decision_id = g.decision_id
