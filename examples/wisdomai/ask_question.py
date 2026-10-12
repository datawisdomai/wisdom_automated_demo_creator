"""Ask a question against a workspace domain and stream the assistant's reply.

Usage:
    python examples/ask_question.py <deployment> <domain_id> "your question here"
"""

import asyncio
import sys

from wisdomai import Client
from wisdomai.subscriptions import subscribe_conversation


async def _print_stream(ws_endpoint: str, token: str, conv_id: str) -> None:
    async for update in subscribe_conversation(ws_endpoint, token, conv_id):
        if update.get("assistantResponseCancelled"):
            print("\n[cancelled]")
            return
        msg = update.get("assistantMessageSent")
        if msg:
            print(f"\n[message {msg['id']} complete]")
            return
        diff = update.get("assistantResponseDiff")
        if diff:
            body_diff = diff.get("bodyDiff") or {}
            for op in body_diff.get("ops") or []:
                ins = op.get("insert")
                if isinstance(ins, str):
                    sys.stdout.write(ins)
                    sys.stdout.flush()


async def run(deployment: str, domain_id: str, question: str) -> None:
    client = Client.for_deployment(deployment)
    token = client.token  # forces the access-key exchange up front
    conv_id = client.create_conversation(domain_id, hidden=False)
    print(f"conversation: {conv_id}\n")

    # Start the subscription first so we don't miss the early diffs.
    sub_task = asyncio.create_task(_print_stream(client.ws_endpoint, token, conv_id))
    await asyncio.sleep(0.5)
    client.send_user_message(conv_id, domain_id, question)
    try:
        await sub_task
    finally:
        client.close()


def main() -> None:
    if len(sys.argv) < 4:
        print(f'Usage: {sys.argv[0]} <deployment> <domain_id> "your question"')
        sys.exit(1)
    asyncio.run(run(sys.argv[1], sys.argv[2], sys.argv[3]))


if __name__ == "__main__":
    main()
