"""List workspace users and (optionally) invite new ones.

    # read (always safe):
    python examples/manage_users.py <deployment>
    python examples/manage_users.py <deployment> --email-search acme.com

    # invite users — dry-run unless --apply:
    python examples/manage_users.py <deployment> \\
        --create alice@acme.com bob@acme.com --apply
    # add --welcome-email to actually send the invite mail.

The read uses `users(input: ListUsersInput)` (NOT `listUsers`, which some docs
claim but the schema does not have). Each user has id, email, name,
creationTimestamp, lastActiveSessionTimestamp, isScimManaged, userAttributes.

⚠️ `create_users` is a WRITE that creates real accounts and, with
--welcome-email, SENDS EMAIL. `set_user_attributes` is also a write. Announce +
confirm (and double-check the email list) before --apply.
"""

from __future__ import annotations

import argparse

from wisdomai import Client


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("deployment")
    ap.add_argument("--email-search", default=None)
    ap.add_argument("--create", nargs="*", default=None, metavar="EMAIL", help="emails to invite")
    ap.add_argument("--welcome-email", action="store_true", help="send the invite email")
    ap.add_argument("--apply", action="store_true", help="actually create the users")
    args = ap.parse_args()

    with Client.for_deployment(args.deployment) as c:
        users = c.list_users(email_search=args.email_search)
        print(f"{len(users)} user(s)"
              + (f" matching {args.email_search!r}" if args.email_search else "") + ":")
        for u in users[:25]:
            scim = "  [scim]" if u.get("isScimManaged") else ""
            print(f"  {u['email']}  ({u.get('name') or '—'}){scim}")
        if len(users) > 25:
            print(f"  ... and {len(users) - 25} more")

        if args.create:
            if not args.apply:
                print(f"\n[dry run] would create_users: {args.create} "
                      f"(send_welcome_email={args.welcome_email})")
                print("re-run with --apply (after announcing the write) to perform it.")
                return
            print(f"\ncreating {len(args.create)} user(s)...")
            c.create_users(args.create, send_welcome_email=args.welcome_email)
            print("done.")

    # Set attributes on an existing user (write):
    #   c.set_user_attributes(user_id, [{"key": "region", "value": "EMEA"}])


if __name__ == "__main__":
    main()
