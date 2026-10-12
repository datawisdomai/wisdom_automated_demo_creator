"""Repo-level configuration: committed `config/*.toml` + per-person secrets in `.env`.

Nothing in `config/` is secret. Secrets (Snowflake PAT, Wisdom API keys) come
only from `.env` at the repo root, loaded once via python-dotenv. Env values
override the toml values so a colleague can point at a different warehouse
without editing committed files.
"""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "config"
DEMOS_DIR = REPO_ROOT / "demos"
DOCS_DIR = REPO_ROOT / "docs"
ENV_PATH = REPO_ROOT / ".env"
DEPLOYMENTS_TOML = CONFIG_DIR / "deployments.toml"
SNOWFLAKE_TOML = CONFIG_DIR / "snowflake.toml"

_env_loaded = False


def load_env() -> bool:
    """Load `.env` from the repo root exactly once. Returns True if it exists."""
    global _env_loaded
    if not _env_loaded:
        load_dotenv(ENV_PATH, override=False)
        _env_loaded = True
    return ENV_PATH.is_file()


@dataclass(frozen=True)
class SnowflakeConfig:
    account: str
    warehouse: str
    ddl_role: str
    read_role: str
    connection_name: str
    user: str | None
    pat: str | None

    @property
    def has_credentials(self) -> bool:
        return bool(self.user and self.pat)


def snowflake_config() -> SnowflakeConfig:
    load_env()
    with SNOWFLAKE_TOML.open("rb") as fh:
        raw = tomllib.load(fh)
    return SnowflakeConfig(
        account=os.getenv("SNOWFLAKE_ACCOUNT") or raw["account"],
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE") or raw["warehouse"],
        ddl_role=os.getenv("SNOWFLAKE_ROLE") or raw["ddl_role"],
        read_role=raw["read_role"],
        connection_name=raw["connection_name"],
        user=os.getenv("SNOWFLAKE_USER") or None,
        pat=os.getenv("SNOWFLAKE_PAT") or None,
    )


def wisdom_deployment(name: str = "proddemo"):
    """The `wisdomai.Deployment` for `name` from the committed registry."""
    from wisdomai import get_deployment

    load_env()
    return get_deployment(name, config_path=DEPLOYMENTS_TOML)


def wisdom_client(name: str = "proddemo", *, timeout: float = 180.0):
    """A `wisdomai.Client` for the named deployment (key from `.env`).

    The default 30 s HTTP timeout is too short for generation mutations such as
    generateWorkflowFromPrompt; 180 s covers every call the pipeline makes."""
    import httpx
    from wisdomai import Client

    load_env()
    client = Client.for_deployment(name, config_path=DEPLOYMENTS_TOML, dotenv_path=ENV_PATH)
    client._http.timeout = httpx.Timeout(timeout)
    return client
