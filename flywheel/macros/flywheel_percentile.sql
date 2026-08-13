-- Warehouse-agnostic percentile. Percentile syntax is the one place the big
-- warehouses genuinely diverge, so it's isolated behind an adapter-dispatched
-- macro rather than smeared through the marts. Default covers Snowflake /
-- Postgres / Redshift; BigQuery and Spark/Databricks override.

{% macro flywheel_percentile(column, p) -%}
    {{ return(adapter.dispatch('flywheel_percentile', 'flywheel')(column, p)) }}
{%- endmacro %}

{% macro default__flywheel_percentile(column, p) -%}
    percentile_cont({{ p }}) within group (order by {{ column }})
{%- endmacro %}

{% macro bigquery__flywheel_percentile(column, p) -%}
    approx_quantiles({{ column }}, 100)[offset({{ (p * 100) | int }})]
{%- endmacro %}

{% macro spark__flywheel_percentile(column, p) -%}
    percentile({{ column }}, {{ p }})
{%- endmacro %}

{% macro databricks__flywheel_percentile(column, p) -%}
    percentile({{ column }}, {{ p }})
{%- endmacro %}
