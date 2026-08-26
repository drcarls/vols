"""Application settings, loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
CONFIG_DIR = REPO_ROOT / "config"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    # --- storage -----------------------------------------------------------
    # SQLite by default. Point at postgresql+psycopg://... to switch; no model
    # code depends on SQLite-specific behaviour.
    database_url: str = f"sqlite:///{DATA_DIR / 'domain_arbitrage.db'}"
    sql_echo: bool = False

    # --- scoring -----------------------------------------------------------
    scoring_config_path: Path = CONFIG_DIR / "scoring_v0.yaml"

    # --- external data providers ------------------------------------------
    # All empty by default. Empty credential => that provider stays disabled and
    # its fields are reported MISSING rather than guessed.
    keyword_provider: str = "null"          # null | csv
    keyword_csv_path: Path | None = None

    buyer_provider: str = "csv"             # null | csv
    buyer_company_csv_path: Path | None = None

    comps_csv_path: Path | None = None      # real comparable sales (e.g. NameBio export)

    dataforseo_login: str = ""
    dataforseo_password: str = ""
    semrush_api_key: str = ""
    ahrefs_api_key: str = ""
    google_ads_developer_token: str = ""

    # --- LLM ---------------------------------------------------------------
    llm_provider: str = "null"              # null | anthropic
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-5"
    llm_max_calls_per_run: int = 200
    llm_cache_enabled: bool = True

    # --- integrity ---------------------------------------------------------
    # Fixture data is synthetic. It exists so the pipeline can be demonstrated
    # end to end. It must never be mistaken for evidence, so it is off unless
    # explicitly enabled, and every record it produces is tagged FIXTURE.
    allow_fixture_data: bool = False

    # --- economics ---------------------------------------------------------
    annual_renewal_cost_usd: float = 11.0
    transaction_cost_rate: float = 0.15     # marketplace commission on sale
    transfer_cost_usd: float = 0.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
