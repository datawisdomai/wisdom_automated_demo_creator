"""Introspect the live WisdomAI GraphQL schema. Read-only.

The published docs cover only ~part of the real schema, so introspection is the
source of truth when you want to discover or verify an operation.

    # counts + every query/mutation/subscription name:
    python examples/introspect_schema.py <deployment>

    # filter operation names by substring:
    python examples/introspect_schema.py <deployment> --grep eval

    # dump one type's fields (or an input type's input fields):
    python examples/introspect_schema.py <deployment> --type EvaluationRun
    python examples/introspect_schema.py <deployment> --type ListUsersInput

Once you've found an operation, add it to the client in two steps:
  1. add the raw GraphQL string to src/wisdomai/operations.py (request only the
     fields you'll use — keep responses lean),
  2. add a thin wrapper method on Client in src/wisdomai/client.py.
See the "Discovering and adding operations" section of the README.
"""

from __future__ import annotations

import argparse

from wisdomai import Client

_ROOT_FIELDS = """
{ __schema {
    queryType { fields { name } }
    mutationType { fields { name } }
    subscriptionType { fields { name } }
} }
"""

_TYPE = """
query T($name: String!) {
  __type(name: $name) {
    kind
    description
    fields(includeDeprecated: true) {
      name
      args { name }
      type { kind name ofType { kind name ofType { kind name ofType { kind name } } } }
    }
    inputFields {
      name
      type { kind name ofType { kind name ofType { kind name } } }
    }
    enumValues { name }
  }
}
"""


def _type_str(t: dict | None) -> str:
    """Flatten a nested GraphQL type ref into something like [User!]!."""
    if not t:
        return "?"
    kind, name, of = t.get("kind"), t.get("name"), t.get("ofType")
    if kind == "NON_NULL":
        return _type_str(of) + "!"
    if kind == "LIST":
        return "[" + _type_str(of) + "]"
    return name or "?"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("deployment")
    ap.add_argument("--grep", default=None, help="filter operation names by substring (case-insensitive)")
    ap.add_argument("--type", dest="type_name", default=None, help="dump a single type's fields")
    args = ap.parse_args()

    with Client.for_deployment(args.deployment) as c:
        if args.type_name:
            t = c.request(_TYPE, {"name": args.type_name})["__type"]
            if t is None:
                raise SystemExit(f"no such type: {args.type_name}")
            print(f"{args.type_name}  ({t['kind']})")
            if t.get("description"):
                print(f"  {t['description']}")
            for f in t.get("fields") or []:
                a = f" ({', '.join(x['name'] for x in f['args'])})" if f.get("args") else ""
                print(f"    {f['name']}{a}: {_type_str(f['type'])}")
            for f in t.get("inputFields") or []:
                print(f"    {f['name']}: {_type_str(f['type'])}")
            for v in t.get("enumValues") or []:
                print(f"    = {v['name']}")
            return

        s = c.request(_ROOT_FIELDS)["__schema"]
        groups = {
            "queries": s["queryType"]["fields"],
            "mutations": s["mutationType"]["fields"],
            "subscriptions": (s.get("subscriptionType") or {}).get("fields") or [],
        }
        print("counts: " + "  ".join(f"{k}={len(v)}" for k, v in groups.items()) + "\n")
        needle = (args.grep or "").lower()
        for label, fields in groups.items():
            names = sorted(f["name"] for f in fields if needle in f["name"].lower())
            if not names:
                continue
            print(f"{label} ({len(names)}{' matching' if needle else ''}):")
            for n in names:
                print(f"  {n}")
            print()


if __name__ == "__main__":
    main()
