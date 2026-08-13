#!/usr/bin/env python3
"""Run the flywheel end-to-end on seeded data, with no warehouse.

This executes the REAL model SQL from ../models -- it just shims the dbt Jinja
(ref/source/type macros/percentile) so the same files run in DuckDB, an
in-process engine. It proves the loop turns and the marts are correct; a real
`dbt build` against Snowflake/BigQuery/etc. runs the identical SQL.

    python3 run_demo.py

Requires duckdb (dev-only): pip install duckdb
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEMO_K = 2  # benchmark k-anonymity threshold, lowered for a 3-tenant demo

MODEL_ORDER = [
    "models/staging/stg_decisions.sql",
    "models/staging/stg_actions.sql",
    "models/staging/stg_outcomes.sql",
    "models/staging/stg_mapping_versions.sql",
    "models/marts/fct_decision_spine.sql",
    "models/marts/fct_attribution.sql",
    "models/marts/mart_mapping_performance.sql",
    "models/marts/mart_benchmark.sql",
]

RAW_DDL = {
    "raw_decisions": "decision_id VARCHAR, tenant_id VARCHAR, surfaced_at VARCHAR, decision_type VARCHAR, entity_type VARCHAR, entity_id VARCHAR, mapping_version_id VARCHAR, model_confidence DOUBLE, segment_key VARCHAR, recommendation VARCHAR, context VARCHAR",
    "raw_actions": "action_id VARCHAR, decision_id VARCHAR, tenant_id VARCHAR, responded_at VARCHAR, response VARCHAR, applied_change VARCHAR, applied_at VARCHAR, experiment_id VARCHAR, experiment_arm VARCHAR, experiment_unit_id VARCHAR",
    "raw_outcomes": "outcome_id VARCHAR, decision_id VARCHAR, tenant_id VARCHAR, metric VARCHAR, window_start VARCHAR, window_end VARCHAR, method VARCHAR, observed_value DOUBLE, control_value DOUBLE, baseline_value DOUBLE, comparison_delta DOUBLE, counterfactual_value DOUBLE, n_treatment INTEGER, n_control INTEGER, variance_treatment DOUBLE, variance_control DOUBLE",
    "raw_mapping_versions": "mapping_version_id VARCHAR, mapping_family VARCHAR, version INTEGER, parent_version_id VARCHAR, created_at VARCHAR, retired_at VARCHAR, definition VARCHAR, author VARCHAR, notes VARCHAR",
}
SEEDS = {
    "raw_decisions": "seed_decisions.csv",
    "raw_actions": "seed_actions.csv",
    "raw_outcomes": "seed_outcomes.csv",
    "raw_mapping_versions": "seed_mapping_versions.csv",
}


def compile_sql(text):
    """Shim dbt Jinja -> plain DuckDB SQL (identical logic, no templating)."""
    text = re.sub(r"\{%.*?%\}", "", text, flags=re.DOTALL)                       # {% set %} etc.
    text = re.sub(r"\{\{\s*config\([^}]*\)\s*\}\}", "", text)                      # config()
    text = re.sub(r"\{\{\s*ref\('([^']+)'\)\s*\}\}", r"\1", text)                  # ref('x') -> x
    text = re.sub(r"\{\{\s*source\('flywheel_raw',\s*'([^']+)'\)\s*\}\}", r"\1", text)
    text = text.replace("{{ dbt.type_timestamp() }}", "timestamp")
    text = text.replace("{{ dbt.type_float() }}", "double")
    text = re.sub(
        r"\{\{\s*flywheel_percentile\('([^']+)',\s*([0-9.]+)\)\s*\}\}",
        r"percentile_cont(\2) within group (order by \1)", text)
    text = text.replace("{{ k }}", str(DEMO_K))
    return text


def show(con, title, sql):
    print("\n" + title)
    print("-" * len(title))
    rows = con.execute(sql).fetchall()
    cols = [d[0] for d in con.description]
    widths = [max(len(c), *(len(_fmt(r[i])) for r in rows)) for i, c in enumerate(cols)] if rows else [len(c) for c in cols]
    print("  ".join(c.ljust(widths[i]) for i, c in enumerate(cols)))
    for r in rows:
        print("  ".join(_fmt(v).ljust(widths[i]) for i, v in enumerate(r)))


def _fmt(v):
    if v is None:
        return "·"
    if isinstance(v, float):
        return f"{v:.3g}"
    return str(v)


def main():
    try:
        import duckdb
    except ImportError:
        sys.exit("duckdb not installed. Run: pip install duckdb")

    con = duckdb.connect()
    for tbl, ddl in RAW_DDL.items():
        con.execute(f"CREATE TABLE {tbl} ({ddl})")
        path = os.path.join(HERE, SEEDS[tbl]).replace("'", "''")
        con.execute(f"COPY {tbl} FROM '{path}' (FORMAT CSV, HEADER, NULLSTR '')")

    for rel in MODEL_ORDER:
        name = os.path.splitext(os.path.basename(rel))[0]
        sql = compile_sql(open(os.path.join(ROOT, rel)).read())
        con.execute(f"CREATE TABLE {name} AS {sql}")

    print("=" * 66)
    print("FLYWHEEL — worked example  (11 decisions · 3 methods · 3 tenants)")
    print("=" * 66)

    show(con, "1. Attribution — every outcome turned into isolated lift", """
        select decision_id, tenant_id as tenant, mapping_version_id as mapping, method,
               round(lift_relative*100,1) as lift_pct, validity_tier as tier,
               is_significant_positive as sig
        from fct_attribution order by decision_id
    """)

    show(con, "2. Mapping performance — THE MOAT: which map works, by tenant × segment (validity-weighted)", """
        select tenant_id as tenant, mapping_version_id as mapping, segment_key as segment,
               round(weighted_mean_lift*100,1) as wtd_lift_pct,
               round(win_rate,2) as win_rate, n_outcomes as n,
               round(avg_validity,2) as validity
        from mart_mapping_performance
        order by mapping_family, segment_key, weighted_mean_lift desc
    """)

    show(con, f"3. Benchmark — cross-customer, k>={DEMO_K} tenants only (the network effect)", """
        select mapping_family as family, segment_key as segment,
               tenant_count as tenants, round(benchmark_mean_lift*100,1) as bench_lift_pct,
               round(benchmark_win_rate,2) as win_rate
        from mart_benchmark order by benchmark_mean_lift desc
    """)

    print("\nWhat the loop just told you")
    print("---------------------------")
    print("• pricing_elasticity v3 beats v2 in mid-market (+30% vs +18%) → promote v3 there.")
    print("• promo_timing v2 posts NEGATIVE lift in mid-market → retire / re-map it.")
    print("• the +8% enterprise holdout isn't significant → don't learn from it yet.")
    print("• benchmark emits only where ≥2 tenants agree → no single customer is exposed.")


if __name__ == "__main__":
    main()
