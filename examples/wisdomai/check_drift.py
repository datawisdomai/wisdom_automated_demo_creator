"""Check the wrapped GraphQL operations against the live schema. Read-only.

The WisdomAI schema evolves — fields get renamed or removed out from under the
client (e.g. `dataSourcesUpdate` was removed). This diffs every root field the
client actually sends (parsed from src/wisdomai/operations.py) against the live
schema and flags any that no longer exist, so drift is a 10-second check instead
of a runtime surprise.

    python examples/check_drift.py <deployment>
    python examples/check_drift.py <deployment> --verbose   # also list unwrapped live ops

Exit code is 1 if any wrapped operation is missing from the live schema (handy
for CI / a pre-flight check), 0 if everything still resolves.
"""

from __future__ import annotations

import argparse
import re
import sys

from wisdomai import Client
from wisdomai import operations as ops

# operation keyword + (name + var decls, no braces) + "{" + first root field.
# The optional `alias:` group skips a response alias (e.g. `id: createConversation`)
# so we capture the real field name, not the alias.
_ROOT_FIELD = re.compile(
    r"\b(?:query|mutation|subscription)\b[^{]*\{\s*"
    r"(?:[A-Za-z_][A-Za-z0-9_]*\s*:\s*)?"
    r"([A-Za-z_][A-Za-z0-9_]*)"
)

_LIVE_FIELDS = """
{ __schema {
    queryType { fields { name } }
    mutationType { fields { name } }
    subscriptionType { fields { name } }
} }
"""


def wrapped_operations() -> dict[str, list[str]]:
    """Map each root field the client sends -> the operations.py constants using it."""
    out: dict[str, list[str]] = {}
    for const_name, value in vars(ops).items():
        if not (const_name.isupper() and isinstance(value, str)):
            continue
        m = _ROOT_FIELD.search(value)
        if not m:
            continue
        field = m.group(1)
        if field.startswith("__"):  # introspection meta field, always present
            continue
        out.setdefault(field, []).append(const_name)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("deployment")
    ap.add_argument("--verbose", action="store_true", help="also summarize unwrapped live ops")
    args = ap.parse_args()

    wrapped = wrapped_operations()

    with Client.for_deployment(args.deployment) as c:
        s = c.request(_LIVE_FIELDS)["__schema"]
    live: set[str] = set()
    counts = {}
    for key in ("queryType", "mutationType", "subscriptionType"):
        fields = (s.get(key) or {}).get("fields") or []
        counts[key] = len(fields)
        live |= {f["name"] for f in fields}

    missing = sorted(f for f in wrapped if f not in live)

    print(f"deployment: {args.deployment}")
    print(f"live schema: queries={counts['queryType']} "
          f"mutations={counts['mutationType']} subscriptions={counts['subscriptionType']}")
    print(f"wrapped operations: {len(wrapped)} root fields\n")

    if missing:
        print(f"✗ DRIFT — {len(missing)} wrapped operation(s) no longer in the schema:")
        for field in missing:
            print(f"   {field}  (used by {', '.join(sorted(wrapped[field]))})")
        print("\nFix: introspect the current schema (examples/introspect_schema.py) "
              "for the replacement, then update operations.py + client.py.")
    else:
        print("✓ no drift — every wrapped operation exists in the live schema.")

    if args.verbose:
        unwrapped = len(live) - len([f for f in wrapped if f in live])
        print(f"\n{unwrapped} live root fields are not wrapped by this client "
              "(reach them via client.request(); see examples/introspect_schema.py).")

    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
