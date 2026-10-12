"""Verify a deployment's impersonation key actually produces a usable session.

Impersonation is a separate permission on a Wisdom API key. A key WITHOUT the
"Impersonator" role still returns a JWT from `impersonateUser` — it just doesn't
authenticate, so every iframe embed silently redirects to /login. This checks
the token rather than trusting that it came back at all.

    .venv/bin/python examples/check_impersonation.py proddemo
    .venv/bin/python examples/check_impersonation.py proddemo --email someone@x.com

Put the impersonator key in .env as `<tenant>_impersonation_key`. Read-only.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys

import httpx

from wisdomai import Client


def claims(jwt: str) -> dict:
    p = jwt.split(".")[1]
    p += "=" * (-len(p) % 4)
    return json.loads(base64.urlsafe_b64decode(p))


def probe(endpoint: str, token: str) -> tuple[bool, str]:
    """Call currentUser with `token` as Bearer. True if it authenticates."""
    r = httpx.post(
        endpoint,
        json={"query": "{ currentUser { id email } }"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    body = r.json()
    if body.get("errors"):
        return False, body["errors"][0].get("message", "?")
    return True, body["data"]["currentUser"]["email"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("deployment")
    ap.add_argument("--email", help="user to impersonate (default: the key's own user)")
    args = ap.parse_args()

    c = Client.for_deployment(args.deployment)
    try:
        # Report the env var actually consulted — a deployment may override it
        # via `key_env` in deployments.toml, so don't assume "<tenant>_key".
        from wisdomai.deployments import get_deployment

        which = (
            f"{c.tenant}_impersonation_key"
            if c.impersonation_key
            else get_deployment(args.deployment).access_key_env
        )
        key = c.impersonation_key or c.access_key
        print(f"deployment  {c.deployment}  ({c.endpoint})")
        print(f"using       {which} = {key[:3]}...{key[-4:]}")
        if not c.impersonation_key:
            print("            (no dedicated <tenant>_impersonation_key set; using "
                  "the ordinary key —\n             fine as long as it carries the "
                  "Impersonator role, which is what this checks)")

        email = args.email or c.current_user()["email"]
        print(f"impersonating {email}\n")

        token = c.impersonate_user(email)
        cl = claims(token)
        print(f"  JWT returned    ...{token[-8:]}  (len {len(token)})")
        print(f"  sub             {cl.get('sub')}")
        print(f"  impersonated_id {cl.get('nsec', {}).get('impersonated_user_id')}")

        ok, detail = probe(c.endpoint, token)
        print()
        if ok:
            print(f"  ✅ token AUTHENTICATES as {detail}")
            print("     Embedding should work: use it as ?token= on an /embed/... URL.")
            return 0
        print(f"  ❌ token REJECTED: {detail}")
        print("     `impersonateUser` returns a JWT even when the key lacks the")
        print("     Impersonator role — that is why embeds bounce to /login.")
        print(f"     Fix: in the UI, Settings → API Keys, find the key with the")
        print(f'     "Impersonator" badge and set {c.tenant}_impersonation_key in .env.')
        return 1
    finally:
        c.close()


if __name__ == "__main__":
    sys.exit(main())
