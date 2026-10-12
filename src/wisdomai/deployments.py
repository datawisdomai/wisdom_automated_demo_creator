"""Deployment registry — maps a friendly name to a WisdomAI tenant.

The registry (``deployments.toml`` by default) holds only non-secret metadata
and is safe to commit. Access keys stay in ``.env``, keyed by ``<tenant>_key``
(or an explicit ``key_env`` per deployment). See ``deployments.toml`` for the
file format.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib  # Python >= 3.11
except ModuleNotFoundError:  # pragma: no cover - 3.10 fallback
    import tomli as tomllib  # type: ignore[no-redef]

from .errors import WisdomAIError

CONFIG_FILENAME = "deployments.toml"


@dataclass(frozen=True)
class Domain:
    """A remembered domain on a deployment.

    Domains are looked up once (``examples/sync_domains.py`` pulls them from
    ``list_domains`` and writes them back into ``deployments.toml``) so you
    don't have to rediscover IDs every session. ``note`` is a free-text
    reminder — it is *not* a safety flag; every write is announced regardless.
    """

    id: str
    name: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class Deployment:
    """One named deployment from the registry."""

    name: str
    tenant: str
    description: str | None = None
    key_env: str | None = None
    host: str | None = None
    domains: tuple[Domain, ...] = ()
    # Workspace that automated demos are published into (proddemo has several
    # workspaces; every domain/connection call must name one explicitly).
    workspace_id: str | None = None
    workspace_name: str | None = None

    @property
    def access_key_env(self) -> str:
        """Name of the env var that holds this deployment's access key."""
        return self.key_env or f"{self.tenant}_key"


def _find_config(config_path: str | os.PathLike[str] | None = None) -> Path:
    """Locate the registry file.

    Order: explicit arg > ``$WISDOMAI_DEPLOYMENTS`` > nearest ``deployments.toml``
    walking up from the cwd.
    """
    if config_path is not None:
        p = Path(config_path)
        if not p.is_file():
            raise WisdomAIError(f"Deployment config not found: {p}")
        return p

    env_path = os.getenv("WISDOMAI_DEPLOYMENTS")
    if env_path:
        p = Path(env_path)
        if not p.is_file():
            raise WisdomAIError(
                f"WISDOMAI_DEPLOYMENTS points at a missing file: {p}"
            )
        return p

    # Walk up from the cwd; accept either `deployments.toml` or the committed
    # `config/deployments.toml` layout used by wisdom_automated_demo_creator.
    # Fall back to the registry shipped next to this package's repo root.
    here = Path(__file__).resolve()
    roots = [Path.cwd(), *Path.cwd().parents, *here.parents]
    for directory in roots:
        for candidate in (directory / CONFIG_FILENAME, directory / "config" / CONFIG_FILENAME):
            if candidate.is_file():
                return candidate

    raise WisdomAIError(
        f"No {CONFIG_FILENAME} found in the cwd or any parent directory. "
        f"Copy {CONFIG_FILENAME}.example -> {CONFIG_FILENAME} and fill it in "
        "(or pass config_path / set WISDOMAI_DEPLOYMENTS)."
    )


def load_deployments(
    config_path: str | os.PathLike[str] | None = None,
) -> dict[str, Deployment]:
    """Parse the registry into ``{name: Deployment}``."""
    path = _find_config(config_path)
    with path.open("rb") as fh:
        data = tomllib.load(fh)

    raw = data.get("deployments")
    if not isinstance(raw, dict):
        raise WisdomAIError(
            f"{path} has no [deployments.*] tables. See the file template."
        )

    out: dict[str, Deployment] = {}
    for name, entry in raw.items():
        if not isinstance(entry, dict) or "tenant" not in entry:
            raise WisdomAIError(
                f"Deployment '{name}' in {path} is missing required 'tenant'."
            )
        domains = tuple(
            Domain(
                id=d["id"],
                name=d.get("name"),
                note=d.get("note"),
            )
            for d in entry.get("domains", [])
            if isinstance(d, dict) and d.get("id")
        )
        out[name] = Deployment(
            name=name,
            tenant=entry["tenant"],
            description=entry.get("description"),
            key_env=entry.get("key_env"),
            host=entry.get("host"),
            domains=domains,
            workspace_id=entry.get("workspace_id"),
            workspace_name=entry.get("workspace_name"),
        )
    return out


def get_deployment(
    name: str,
    config_path: str | os.PathLike[str] | None = None,
) -> Deployment:
    """Look up a single deployment by name, with a helpful error if absent."""
    deployments = load_deployments(config_path)
    try:
        return deployments[name]
    except KeyError:
        known = ", ".join(sorted(deployments)) or "(none)"
        raise WisdomAIError(
            f"Unknown deployment '{name}'. Known deployments: {known}."
        ) from None


def list_deployment_names(
    config_path: str | os.PathLike[str] | None = None,
) -> list[str]:
    """Names of all registered deployments, sorted."""
    return sorted(load_deployments(config_path))
