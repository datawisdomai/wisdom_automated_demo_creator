"""List dashboards visible to the current user.

Run: python examples/list_dashboards.py <deployment> [scope]
  scope defaults to VIEWER. Common values: VIEWER, EDITOR, OWNER.
"""

import sys

from wisdomai import Client


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <deployment> [scope]")
        sys.exit(1)
    deployment = sys.argv[1]
    scope = sys.argv[2] if len(sys.argv) > 2 else "VIEWER"
    with Client.for_deployment(deployment) as client:
        nodes = client.dashboards(scope=scope)
        print(f"Found {len(nodes)} dashboards at scope={scope}:\n")
        for d in nodes:
            owner = (d.get("owner") or {}).get("email", "?")
            domains = ", ".join((dom.get("name") or "?") for dom in d.get("domains") or [])
            print(f"  {d['id']}  {d['name']}")
            print(f"    owner={owner}  domains=[{domains}]  access={d['accessLevel']}")


if __name__ == "__main__":
    main()
