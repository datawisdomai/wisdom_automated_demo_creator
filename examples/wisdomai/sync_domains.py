"""Remember a deployment's domains in deployments.toml so you don't rediscover
them every session.

Pulls `list_domains()` for a deployment and writes the results into the
`[[deployments.<name>.domains]]` blocks of your local deployments.toml. Any
`note` you've hand-written on an existing domain is preserved; everything else
is refreshed from the live list.

    python examples/sync_domains.py <deployment>                 # all visible domains
    python examples/sync_domains.py <deployment> --filter prod   # only names containing "prod"
    python examples/sync_domains.py <deployment> --include-hidden

NB: deployments.toml is your local, gitignored file. This script rewrites it
with a structured TOML dump, so hand-written *comments* are not preserved (the
human-facing guidance lives in the committed deployments.toml.example). Your
connection fields and domain notes are kept.
"""

from __future__ import annotations

import argparse

import tomli_w

try:
    import tomllib  # Python >= 3.11
except ModuleNotFoundError:  # pragma: no cover - 3.10 fallback
    import tomli as tomllib  # type: ignore[no-redef]

from wisdomai import Client
from wisdomai.deployments import _find_config


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("deployment")
    ap.add_argument(
        "--filter",
        dest="name_filter",
        default=None,
        help="only remember domains whose name contains this substring (case-insensitive)",
    )
    ap.add_argument(
        "--include-hidden",
        action="store_true",
        help="also remember domains flagged isHidden",
    )
    args = ap.parse_args()

    config_path = _find_config()
    with config_path.open("rb") as fh:
        data = tomllib.load(fh)

    block = (data.get("deployments") or {}).get(args.deployment)
    if block is None:
        raise SystemExit(
            f"Deployment '{args.deployment}' is not in {config_path}. "
            "Add its [deployments.*] block first."
        )

    # Carry forward any hand-written notes, keyed by domain id.
    existing_notes = {
        d["id"]: d["note"]
        for d in block.get("domains", [])
        if isinstance(d, dict) and d.get("id") and d.get("note")
    }

    with Client.for_deployment(args.deployment) as c:
        domains = c.list_domains()

    needle = (args.name_filter or "").lower()
    remembered: list[dict] = []
    for d in sorted(domains, key=lambda x: (x["name"] or "").lower()):
        if d.get("isHidden") and not args.include_hidden:
            continue
        if needle and needle not in (d["name"] or "").lower():
            continue
        entry = {"id": d["id"], "name": d["name"]}
        if d["id"] in existing_notes:
            entry["note"] = existing_notes[d["id"]]
        remembered.append(entry)

    block["domains"] = remembered
    with config_path.open("wb") as fh:
        tomli_w.dump(data, fh)

    print(f"remembered {len(remembered)} domain(s) for '{args.deployment}' in {config_path}")
    for e in remembered[:20]:
        note = f"  # {e['note']}" if e.get("note") else ""
        print(f"  {e['id']}  {e['name']}{note}")
    if len(remembered) > 20:
        print(f"  ... and {len(remembered) - 20} more")


if __name__ == "__main__":
    main()
