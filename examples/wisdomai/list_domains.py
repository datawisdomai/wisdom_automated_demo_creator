"""List the domains on a deployment — handy for grabbing real domain IDs before
any write (each deployment has its own domains). To remember these IDs across
sessions, run `examples/sync_domains.py <deployment>`.

Run from repo root after `pip install -e .`:
    python examples/list_domains.py <deployment>
    python examples/list_domains.py            # single-tenant path via from_env
"""

import sys

from wisdomai import Client


def main() -> None:
    if len(sys.argv) > 1:
        client = Client.for_deployment(sys.argv[1])
    else:
        client = Client.from_env()

    with client:
        print(f"Endpoint: {client.endpoint}")
        if client.domains:
            print(f"{len(client.domains)} domain(s) remembered in deployments.toml")
        print()

        domains = client.list_domains()
        print(f"{len(domains)} domain(s):\n")
        for d in sorted(domains, key=lambda x: x["updatedAt"], reverse=True):
            hidden = "  [hidden]" if d.get("isHidden") else ""
            print(f"  {d['updatedAt'][:19]}  {d['id']}")
            print(f"      {d['name']}{hidden}")


if __name__ == "__main__":
    main()
