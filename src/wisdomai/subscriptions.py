"""Async helper for `subscribeConversation` over WebSockets.

proddemo now negotiates the modern `graphql-transport-ws` protocol (the legacy
`graphql-ws` handshake is rejected with 4406 "Subprotocol not acceptable",
verified 2026-10-12). Both are implemented; the modern one is tried first.
"""

from __future__ import annotations

import json
import uuid
from typing import AsyncIterator

import websockets

from . import operations as ops


async def _transport_ws(ws_endpoint: str, token: str, conversation_id: str) -> AsyncIterator[dict]:
    async with websockets.connect(ws_endpoint, subprotocols=["graphql-transport-ws"],
                                  additional_headers={"Authorization": f"Bearer {token}"}) as ws:
        await ws.send(json.dumps({"type": "connection_init", "payload": {"Authorization": f"Bearer {token}", "token": token}}))
        sub_id = str(uuid.uuid4())
        acked = False
        while True:
            msg = json.loads(await ws.recv())
            t = msg.get("type")
            if t == "connection_ack" and not acked:
                acked = True
                await ws.send(json.dumps({"id": sub_id, "type": "subscribe", "payload": {
                    "query": ops.SUBSCRIBE_CONVERSATION,
                    "variables": {"auth": {"token": token}, "conversationId": conversation_id}}}))
            elif t == "ping":
                await ws.send(json.dumps({"type": "pong"}))
            elif t == "next":
                payload = msg.get("payload", {})
                if payload.get("errors"):
                    raise RuntimeError(f"Subscription error: {payload['errors']}")
                yield payload.get("data", {}).get("subscribeConversation", {}) or {}
            elif t == "error":
                raise RuntimeError(f"Subscription error: {msg.get('payload')}")
            elif t == "complete":
                break


async def _legacy_ws(ws_endpoint: str, token: str, conversation_id: str) -> AsyncIterator[dict]:
    async with websockets.connect(ws_endpoint, subprotocols=["graphql-ws"],
                                  additional_headers={"Authorization": f"Bearer {token}"}) as ws:
        await ws.send(json.dumps({"type": "connection_init", "payload": {}}))
        sub_id = str(uuid.uuid4())
        await ws.send(json.dumps({"id": sub_id, "type": "start", "payload": {
            "query": ops.SUBSCRIBE_CONVERSATION,
            "variables": {"auth": {"token": token}, "conversationId": conversation_id}}}))
        while True:
            msg = json.loads(await ws.recv())
            t = msg.get("type")
            if t == "data":
                payload = msg.get("payload", {})
                if payload.get("errors"):
                    raise RuntimeError(f"Subscription error: {payload['errors']}")
                yield payload.get("data", {}).get("subscribeConversation", {}) or {}
            elif t == "error":
                raise RuntimeError(f"Subscription error: {msg.get('payload')}")
            elif t == "complete":
                break


async def subscribe_conversation(ws_endpoint: str, token: str, conversation_id: str) -> AsyncIterator[dict]:
    """Yield ConversationUpdateOneOf payloads until the server completes the stream."""
    try:
        async for update in _transport_ws(ws_endpoint, token, conversation_id):
            yield update
        return
    except websockets.exceptions.InvalidStatus as exc:  # server refused the modern protocol
        if "4406" not in str(exc) and "subprotocol" not in str(exc).lower():
            raise
    except websockets.exceptions.ConnectionClosedError as exc:
        if exc.rcvd is None or exc.rcvd.code != 4406:
            raise
    async for update in _legacy_ws(ws_endpoint, token, conversation_id):
        yield update
