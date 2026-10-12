"""The experiences a demo ships beyond data and context: an answered follow-up
chat, a Live App built from one prompt, and a disabled agent built from one prompt.

Chat: create a visible conversation, send the question, collect the streamed
answer over the graphql-ws subscription (pattern from examples/wisdomai/ask_question.py).
Agent: generateWorkflowFromPrompt -> createWorkflowAgent(asDraft=True) so it exists
with its prompt but never runs.
"""
from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass, field

from wisdomai import Client, GraphQLError
from wisdomai.subscriptions import subscribe_conversation

from .manifest import State
from .spec import DemoSpec


# ---------------------------------------------------------------- chat
@dataclass
class ChatAnswer:
    conversation_id: str
    question: str
    text: str
    seconds: float
    completed: bool
    hits: list[str] = field(default_factory=list)
    misses: list[str] = field(default_factory=list)

    @property
    def score(self) -> float | None:
        n = len(self.hits) + len(self.misses)
        return None if n == 0 else len(self.hits) / n


def _extract_text(ops: list[dict]) -> str:
    out = []
    for op in ops or []:
        ins = op.get("insert")
        if isinstance(ins, str):
            out.append(ins)
        elif isinstance(ins, dict):
            out.append(ins.get("text") or ins.get("externalMarkdownText") or "")
    return "".join(out)


async def _collect(ws_endpoint: str, token: str, conv_id: str, timeout_s: float) -> tuple[str, bool]:
    chunks: list[str] = []
    final: str | None = None

    async def stream():
        nonlocal final
        async for update in subscribe_conversation(ws_endpoint, token, conv_id):
            if update.get("assistantResponseCancelled"):
                return
            msg = update.get("assistantMessageSent")
            if msg:
                final = _extract_text((msg.get("body") or {}).get("ops") or [])
                return
            diff = update.get("assistantResponseDiff")
            if diff:
                chunks.append(_extract_text((diff.get("bodyDiff") or {}).get("ops") or []))

    try:
        await asyncio.wait_for(stream(), timeout=timeout_s)
        return (final if final else "".join(chunks)), True
    except asyncio.TimeoutError:
        return "".join(chunks), False
    except Exception as exc:  # noqa: BLE001 — socket refused/closed: fall back to polling the messages
        raise _SocketUnavailable(str(exc)[:200]) from exc


class _SocketUnavailable(RuntimeError):
    pass


def poll_answer(client: Client, conversation_id: str, *, timeout_s: float, poll_s: float = 10.0,
                settle_polls: int = 2) -> tuple[str, bool]:
    """Read the conversation until an assistant message exists and stops changing."""
    deadline = time.time() + timeout_s
    last, stable = "", 0
    while time.time() < deadline:
        msgs = client.chat_messages(conversation_id)
        texts = [_extract_text((m.get("body") or {}).get("ops") or []) for m in msgs if str(m.get("sender", "")).upper() == "ASSISTANT"]
        text = texts[-1] if texts else ""
        if text and text == last:
            stable += 1
            if stable >= settle_polls:
                return text, True
        else:
            stable = 0
        last = text
        time.sleep(poll_s)
    return last, False


def _judge(text: str, expected_points: list[str]) -> tuple[list[str], list[str]]:
    """Cheap lexical check: a point counts as hit when most of its distinctive
    tokens (names, numbers) appear in the answer. Claude does the real judgement
    in /run-step chat; this just flags obvious misses."""
    low = text.lower()
    hits, misses = [], []
    for point in expected_points:
        tokens = [t for t in re.findall(r"[A-Za-z][A-Za-z\-']{3,}|\d+(?:\.\d+)?", point) if t.lower() not in _STOP]
        if not tokens:
            continue
        found = sum(1 for t in tokens if t.lower() in low)
        (hits if found >= max(1, round(0.6 * len(tokens))) else misses).append(point)
    return hits, misses


_STOP = {"about", "with", "from", "that", "this", "than", "versus", "there", "their", "which", "over", "percent", "points", "point",
         "recent", "prior", "weeks", "week", "main", "driver", "rising", "down", "customer", "customers", "window", "renewal"}


def ask_followup(client: Client, spec: DemoSpec, state: State, *, question: str | None = None, timeout_s: float = 420,
                 hidden: bool = False) -> ChatAnswer:
    domain_id = state.wisdom["domain_id"]
    question = question or spec.chat.get("followup_question")
    if not question:
        raise ValueError("chat.followup_question is not set in demo.yaml")
    token = client.token
    conv_id = client.create_conversation(domain_id, hidden=hidden)
    t0 = time.time()

    async def run():
        task = asyncio.create_task(_collect(client.ws_endpoint, token, conv_id, timeout_s))
        await asyncio.sleep(0.5)
        client.send_user_message(conv_id, domain_id, question)
        return await task

    try:
        text, completed = asyncio.run(run())
    except _SocketUnavailable:
        text, completed = poll_answer(client, conv_id, timeout_s=timeout_s - (time.time() - t0))
    hits, misses = _judge(text, list(spec.chat.get("expected_points") or []))
    ans = ChatAnswer(conv_id, question, text, round(time.time() - t0, 1), completed, hits, misses)
    convs = list(state.wisdom.get("conversations") or [])
    convs.append({"id": conv_id, "question": question, "completed": completed, "score": ans.score, "chars": len(text)})
    state.set("wisdom", "conversations", convs[-10:])
    state.set("wisdom", "followup_conversation_id", conv_id)
    return ans


# ---------------------------------------------------------------- agent
@dataclass
class AgentResult:
    agent_id: str
    name: str
    is_draft: bool
    schedule_id: str | None
    workflow_nodes: int
    message: str = ""


_NODE_TYPES = {"SCHEDULE_TRIGGER": "TRIGGER_CORE", "TRIGGER": "TRIGGER_CORE", "TRIGGER_CORE": "TRIGGER_CORE",
               "DATA_FETCH": "DATA_FETCH", "DATA_WEB_SEARCH": "DATA_WEB_SEARCH", "DATA_MCP": "DATA_MCP",
               "REASONING": "REASONING", "REASONING_ANALYSIS": "REASONING_ANALYSIS", "CONTROL_IF_ELSE": "CONTROL_IF_ELSE",
               "CONTROL_SWITCH": "CONTROL_SWITCH", "CONTROL_LOOP": "CONTROL_LOOP", "ARTIFACT_BUILDER": "ARTIFACT_BUILDER",
               "ACTION": "ACTION", "EXPORT": "EXPORT", "EMAIL": "ACTION", "SLACK": "ACTION", "TEAMS": "ACTION", "WEBHOOK": "ACTION"}
_TITLES = {"TRIGGER_CORE": "Schedule", "DATA_FETCH": "Fetch data", "DATA_WEB_SEARCH": "Web search", "DATA_MCP": "MCP data",
           "REASONING": "Reason", "REASONING_ANALYSIS": "Analyse", "CONTROL_IF_ELSE": "If / else", "CONTROL_SWITCH": "Switch",
           "CONTROL_LOOP": "Loop", "ARTIFACT_BUILDER": "Build artifact", "ACTION": "Send", "EXPORT": "Export"}


def _delta(text: str) -> dict:
    return {"ops": [{"insert": {"text": text or ""}}]}


def convert_workflow(generated: dict, *, domain_id: str, default_email: str | None = None) -> dict:
    """Turn generateWorkflowFromPrompt's visualizer JSON into an ``AgentWorkflowInput``.

    Verified against proddemo 2026-10-12: the generated nodes carry UI-only keys
    (``scheduleConfig``, ``branchEdges``, ``deliveryConfig``, ``NOTE``/``email`` types)
    that the input type expresses as ``config`` / ``routeMap`` / canvas notes."""
    nodes_out, notes = [], []
    counts: dict[str, int] = {}
    for n in generated.get("nodes") or []:
        raw_type = str(n.get("type") or "").upper()
        if raw_type == "NOTE":
            notes.append({"id": n["id"], "text": n.get("instruction") or n.get("text") or "", "positionX": float(n.get("positionX") or 0), "positionY": float(n.get("positionY") or 0)})
            continue
        ntype = _NODE_TYPES.get(raw_type)
        if ntype is None:
            raise ValueError(f"unknown generated node type {raw_type!r}")
        counts[ntype] = counts.get(ntype, 0) + 1
        title = n.get("title") or _TITLES[ntype] + (f" {counts[ntype]}" if counts[ntype] > 1 else "")
        config: dict = {}
        if ntype == "TRIGGER_CORE":
            sc = n.get("scheduleConfig") or {}
            config["triggerType"] = "SCHEDULE" if sc else "MANUAL"
            if sc:
                config["timing"] = {"intervalInMins": int(sc.get("intervalInMins") or 1440), "startTime": sc.get("startTime") or "2026-01-01T07:00:00",
                                    "cronExpression": sc.get("cronExpression"), "cronTimezone": sc.get("cronTimezone")}
        if raw_type in ("EMAIL", "SLACK", "TEAMS", "WEBHOOK") or n.get("deliveryConfig") is not None:
            dc = n.get("deliveryConfig") or {}
            kind = raw_type if raw_type in ("EMAIL", "SLACK", "TEAMS", "WEBHOOK") else "EMAIL"
            delivery: dict = {"type": kind}
            if kind == "EMAIL":
                delivery["emailConfig"] = {"toEmailIds": list(dc.get("toEmailIds") or ([default_email] if default_email else []))}
            elif kind == "SLACK":
                delivery["slackConfig"] = {"channelNames": list(dc.get("channelNames") or [])}
            config["delivery"] = delivery
        if n.get("branchEdges"):
            # The server rejects route entries with an empty condition (the implicit
            # "else" branch); only conditioned branches go in the routeMap.
            config["routeMap"] = [{"condition": _delta(b.get("condition")), "edgeId": b["edgeId"], "branchIndex": int(b.get("branchIndex") or 0)}
                                  for b in n["branchEdges"] if (b.get("condition") or "").strip()]
        if ntype in ("DATA_FETCH", "REASONING_ANALYSIS", "REASONING"):
            config["domainId"] = domain_id
        node = {"id": n["id"], "type": ntype, "title": title, "instruction": _delta(n.get("instruction") or title),
                "positionX": float(n.get("positionX") or 0), "positionY": float(n.get("positionY") or 0)}
        if config:
            node["config"] = config
        if n.get("handle"):
            node["handle"] = n["handle"]
        nodes_out.append(node)
    node_ids = {n["id"] for n in nodes_out}
    edges = [{"id": e["id"], "fromNodeId": e["fromNodeId"], "toNodeId": e["toNodeId"]} for e in (generated.get("edges") or [])
             if e.get("fromNodeId") in node_ids and e.get("toNodeId") in node_ids]
    out = {"nodes": nodes_out, "edges": edges}
    if notes:
        out["canvasAnnotation"] = {"notes": notes}
    return out


def create_agent(client: Client, spec: DemoSpec, state: State, *, workspace_id: str, default_email: str | None = None) -> AgentResult:
    """Generate the workflow from the agent prompt (cached in build/agent_workflow.json),
    convert it to the input shape, create it as a DRAFT (never scheduled), read it back."""
    domain_id = state.wisdom["domain_id"]
    name = spec.agent.get("name") or f"{spec.title} agent"
    prompt_path = spec.dir / spec.agent.get("prompt", "agent_prompt.md")
    prompt = _prompt_body(prompt_path.read_text())
    cache = spec.paths.ensure().build / "agent_workflow.json"
    gen = None
    if cache.is_file():
        try:
            cached = json.loads(cache.read_text())
            if cached.get("workflow"):
                gen = {"workflowJson": json.dumps(cached["workflow"]), "agentName": cached.get("agentName"), "message": cached.get("message", "")}
        except (ValueError, KeyError):
            gen = None
    if gen is None:
        gen = client.generate_workflow_from_prompt(prompt, domain_id=domain_id, workspace_id=workspace_id)
        if gen.get("workflowJson"):
            cache.write_text(json.dumps({"agentName": gen.get("agentName"), "message": gen.get("message"), "workflow": json.loads(gen["workflowJson"])}, indent=2))
    workflow_json = gen.get("workflowJson")
    if not workflow_json:
        raise RuntimeError(f"generateWorkflowFromPrompt returned no workflow: {gen.get('message', '')[:300]}")
    workflow = convert_workflow(json.loads(workflow_json), domain_id=domain_id, default_email=default_email)
    nodes = workflow["nodes"]
    spec_input = {
        "analysisDomainId": domain_id,
        "agentName": name,
        "analysisDescription": (gen.get("message") or prompt)[:4000],
        "useDeepAnalysis": False,
        "instruction": prompt[:4000],
        "workflow": workflow,
    }
    created = client.create_workflow_agent(spec_input, workspace_id=workspace_id, as_draft=True)
    agent_id = created["id"]
    back = client.get_agent(agent_id, workspace_id=workspace_id) or created
    if back.get("scheduleId") and not back.get("isDraft"):
        client.update_agent_state(agent_id, "INACTIVE", reason="demo creator: created disabled")
        back = client.get_agent(agent_id, workspace_id=workspace_id) or back
    state.set("wisdom", "agent_id", agent_id)
    state.set("wisdom", "agent_name", name)
    return AgentResult(agent_id, name, bool(back.get("isDraft")), back.get("scheduleId"), len(nodes), gen.get("message", ""))


def _prompt_body(md: str) -> str:
    """The prompt inside the first ``` fenced block, else the whole file minus headings."""
    m = re.search(r"```[a-z]*\n(.*?)```", md, re.S)
    if m:
        return m.group(1).strip()
    return "\n".join(l for l in md.splitlines() if not l.startswith("#")).strip()


# ---------------------------------------------------------------- live app
@dataclass
class LiveAppResult:
    app_id: str
    name: str
    conversation_id: str
    dashboard_id: str
    completed: bool
    seconds: float
    assistant_text: str = ""
    live_spec_version: int | None = None
    has_unpublished_changes: bool | None = None


def create_live_app(client: Client, spec: DemoSpec, state: State, *, workspace_id: str, timeout_s: float = 1500,
                    echo: bool = True) -> LiveAppResult:
    """Mirror the UI: createApp -> conversation with liveAppEditPolicy EDIT ->
    setActiveAppConversation -> one prompt message carrying the app's dashboard
    reference -> wait for the assistant to finish -> read the app back."""
    domain_id = state.wisdom["domain_id"]
    name = spec.live_app.get("name") or f"{spec.title} Live App"
    prompt = _prompt_body((spec.dir / spec.live_app.get("prompt", "live_app_prompt.md")).read_text())
    if state.wisdom.get("app_id") and not state.wisdom.get("app_conversation_id"):
        app = client.get_app_full(state.wisdom["app_id"])  # shell exists from an earlier attempt; build into it
    else:
        app = client.create_app(workspace_id, name, domain_id)
    app_id, dashboard_id = app["id"], app["dashboardId"]
    state.set("wisdom", "app_id", app_id)
    state.set("wisdom", "app_name", name)
    conv_id = client.create_conversation_full(domain_id, hidden=False, workspace_id=workspace_id, live_app_edit_policy="EDIT",
                                              request_channel_type="LIVE_APP", channel_source_id=app_id)
    state.set("wisdom", "app_conversation_id", conv_id)
    try:
        client.set_active_app_conversation(app_id, conv_id)
    except GraphQLError as exc:  # not fatal: the dashboard reference on the message still targets the app
        if echo:
            print(f"  note: setActiveAppConversation failed: {str(exc)[:160]}")
    token = client.token
    t0 = time.time()

    async def run():
        task = asyncio.create_task(_collect(client.ws_endpoint, token, conv_id, timeout_s))
        await asyncio.sleep(0.5)
        client.send_live_app_prompt(conv_id, domain_id, prompt, workspace_id=workspace_id, dashboard_id=dashboard_id,
                                    dashboard_version=int(app.get("dashboardVersion") or 0),
                                    dashboard_sub_version=str(app.get("dashboardSubVersion") or ""))
        return await task

    try:
        text, completed = asyncio.run(run())
    except _SocketUnavailable:
        text, completed = poll_answer(client, conv_id, timeout_s=timeout_s - (time.time() - t0), poll_s=20, settle_polls=3)
    back = client.get_app_full(app_id)
    return LiveAppResult(app_id, name, conv_id, dashboard_id, completed, round(time.time() - t0, 1), text,
                         back.get("liveSpecVersion"), back.get("hasUnpublishedChanges"))
