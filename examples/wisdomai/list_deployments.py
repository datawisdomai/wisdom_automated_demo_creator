"""List the WisdomAI deployments registered in deployments.toml.

Shows which deployments are known and whether each one's access key is present
in .env — handy at the start of a session to pick what you're working on.

Run: python examples/list_deployments.py
"""

import os

from dotenv import load_dotenv

from wisdomai import load_deployments


def main() -> None:
    load_dotenv()
    deployments = load_deployments()
    if not deployments:
        print("No deployments registered. Add one to deployments.toml.")
        return

    print(f"{len(deployments)} deployment(s) registered:\n")
    for name, dep in sorted(deployments.items()):
        has_key = "✓ key" if os.getenv(dep.access_key_env) else "✗ NO KEY"
        host = dep.host or f"{dep.tenant}.askwisdom.ai"
        print(f"  {name}")
        print(f"    tenant={dep.tenant}  https://{host}/graphql")
        if dep.description:
            print(f"    {dep.description}")
        print(f"    key_env={dep.access_key_env} [{has_key}]")
        if dep.domains:
            print(f"    {len(dep.domains)} remembered domain(s)  (run sync_domains.py to refresh)")
        else:
            print("    no remembered domains  (run: python examples/sync_domains.py "
                  f"{name})")
        print()


if __name__ == "__main__":
    main()
