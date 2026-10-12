"""Smoke test: connect to the workspace and print the current user + dashboards.

The access-key -> JWT exchange happens transparently on the first call.

Run from repo root after `pip install -e .`:
    python examples/smoke_test.py
"""

from wisdomai import Client


def main() -> None:
    with Client.from_env() as client:
        print(f"Endpoint: {client.endpoint}\n")

        me = client.current_user()
        print(f"Connected as: {me['email']}  (id={me['id']})")

        dashes = client.dashboards(scope="VIEWER")
        print(f"Visible dashboards: {len(dashes)}")
        for d in dashes[:5]:
            print(f"  - {d['name']}")


if __name__ == "__main__":
    main()
