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


def _first_key(entries: list[dict]) -> str | None:
    return entries[0].get("key") if entries else None


def ask_followup(client: Client, spec: DemoSpec, state: State, *, question: str | None = None, timeout_s: float = 420,
                 hidden: bool = False, entry: dict | None = None) -> ChatAnswer:
    """Ask one chat question (`entry` = one of spec.chats, default the first) in a visible conversation
    and judge the answer against the entry's expected_points. Per-entry ids live in state
    `wisdom.chats[<key>]`; the first entry is mirrored into the legacy `followup_conversation_id`."""
    domain_id = state.wisdom["domain_id"]
    entry = entry or spec.chat
    key = entry.get("key") or _first_key(spec.chats) or "followup"
    question = question or entry.get("followup_question") or entry.get("question")
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
    hits, misses = _judge(text, list(entry.get("expected_points") or []))
    ans = ChatAnswer(conv_id, question, text, round(time.time() - t0, 1), completed, hits, misses)
    convs = list(state.wisdom.get("conversations") or [])
    convs.append({"id": conv_id, "question": question, "completed": completed, "score": ans.score, "chars": len(text)})
    state.set("wisdom", "conversations", convs[-10:])
    chats = dict(state.wisdom.get("chats") or {})
    chats[key] = {"conversation_id": conv_id, "question": question, "score": ans.score, "completed": completed}
    state.set("wisdom", "chats", chats)
    if key == (_first_key(spec.chats) or key):
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


def _clean_delta(d: dict | None, fallback: str = "") -> dict:
    """Output Delta -> DeltaInput: keep text inserts only (the input type has no trajectory/visualization elements)."""
    ops = []
    for op in (d or {}).get("ops") or []:
        ins = op.get("insert") or {}
        if isinstance(ins, dict) and ins.get("text") is not None:
            ops.append({"insert": {"text": ins["text"]}})
    return {"ops": ops or [{"insert": {"text": fallback}}]}


def specification_to_input(generated: dict, *, domain_id: str, default_email: str | None = None) -> dict:
    """Turn generateWorkflowFromPrompt's `specification` (AnalysisScheduleTask, 2026-10 shape) into the
    AnalysisScheduleTaskInput for createWorkflowAgent: drop nulls, reduce deltas to text, default the
    domain id and an empty email recipient list."""
    wf = generated.get("workflow") or {}
    nodes = []
    for n in wf.get("nodes") or []:
        node = {"id": n["id"], "type": n["type"], "title": n.get("title") or n["type"], "instruction": _clean_delta(n.get("instruction"), n.get("title") or ""),
                "positionX": float(n.get("positionX") or 0), "positionY": float(n.get("positionY") or 0)}
        if n.get("handle"):
            node["handle"] = n["handle"]
        cfg_in = n.get("config") or {}
        cfg: dict = {}
        if cfg_in.get("domainId") or n["type"] in ("DATA_FETCH", "REASONING_ANALYSIS", "REASONING"):
            cfg["domainId"] = cfg_in.get("domainId") or domain_id
        if cfg_in.get("triggerType"):
            cfg["triggerType"] = cfg_in["triggerType"]
        if cfg_in.get("timing"):
            cfg["timing"] = {k: v for k, v in cfg_in["timing"].items() if v is not None}
        if cfg_in.get("delivery"):
            d = cfg_in["delivery"]
            delivery = {"type": d["type"]}
            if d.get("emailConfig") is not None or d["type"] == "EMAIL":
                to = list((d.get("emailConfig") or {}).get("toEmailIds") or [])
                delivery["emailConfig"] = {"toEmailIds": to or ([default_email] if default_email else [])}
            if d.get("slackConfig"):
                delivery["slackConfig"] = {"channelNames": list(d["slackConfig"].get("channelNames") or [])}
            if d.get("teamsConfig"):
                delivery["teamsConfig"] = {"userEmails": list(d["teamsConfig"].get("userEmails") or [])}
            if d.get("webhookConfig"):
                delivery["webhookConfig"] = {"webhookUrls": list(d["webhookConfig"].get("webhookUrls") or [])}
            cfg["delivery"] = delivery
        if cfg_in.get("routeMap"):
            cfg["routeMap"] = [{"condition": _clean_delta(r.get("condition")), "edgeId": r["edgeId"], "branchIndex": int(r.get("branchIndex") or 0)}
                               for r in cfg_in["routeMap"] if _clean_delta(r.get("condition"))["ops"][0]["insert"]["text"].strip()]
        if cfg:
            node["config"] = cfg
        nodes.append(node)
    node_ids = {n["id"] for n in nodes}
    edges = [{"id": e["id"], "fromNodeId": e["fromNodeId"], "toNodeId": e["toNodeId"]} for e in (wf.get("edges") or [])
             if e.get("fromNodeId") in node_ids and e.get("toNodeId") in node_ids]
    out = {"nodes": nodes, "edges": edges}
    notes = ((wf.get("canvasAnnotation") or {}).get("notes")) or []
    if notes:
        out["canvasAnnotation"] = {"notes": [{"id": x["id"], "text": x.get("text") or "", "positionX": float(x.get("positionX") or 0), "positionY": float(x.get("positionY") or 0)} for x in notes]}
    return out


def create_agent(client: Client, spec: DemoSpec, state: State, *, workspace_id: str, default_email: str | None = None,
                 entry: dict | None = None) -> AgentResult:
    """Generate the workflow from the agent prompt (cached in build/agent_workflow[_<key>].json),
    convert it to the input shape, create it as a DRAFT (never scheduled), read it back.
    `entry` is one of spec.agents (default the first); ids go to state `wisdom.agents[<key>]`,
    the first entry also to the legacy `agent_id` / `agent_name`."""
    domain_id = state.wisdom["domain_id"]
    entry = entry or spec.agent
    key = entry.get("key") or _first_key(spec.agents) or "agent"
    first = key == (_first_key(spec.agents) or key)
    name = entry.get("name") or f"{spec.title} agent"
    prompt_path = spec.dir / entry.get("prompt", "agent_prompt.md")
    prompt = _prompt_body(prompt_path.read_text())
    cache = spec.paths.ensure().build / ("agent_workflow.json" if first else f"agent_workflow_{key}.json")
    gen = None
    if cache.is_file():
        try:
            cached = json.loads(cache.read_text())
            if cached.get("specification") or cached.get("workflow"):
                gen = cached
        except (ValueError, KeyError):
            gen = None
    if gen is None:
        gen = client.generate_workflow_from_prompt(prompt, domain_id=domain_id, workspace_id=workspace_id, agent_name=name)
        if gen.get("specification") or gen.get("workflowJson"):
            cache.write_text(json.dumps({"agentName": gen.get("agentName"), "message": gen.get("message"), "specification": gen.get("specification"),
                                         "workflow": json.loads(gen["workflowJson"]) if gen.get("workflowJson") else None}, indent=2))
    if gen.get("specification"):
        # 2026-10 API: the generator already returns an AnalysisScheduleTask
        gs = gen["specification"]
        workflow = specification_to_input(gs, domain_id=domain_id, default_email=default_email)
        description = gs.get("analysisDescription") or gen.get("message") or prompt
        instruction = gs.get("instruction") or prompt
    else:
        workflow_json = gen.get("workflowJson") or (json.dumps(gen["workflow"]) if gen.get("workflow") else None)
        if not workflow_json:
            raise RuntimeError(f"generateWorkflowFromPrompt returned no workflow: {gen.get('message', '')[:300]}")
        workflow = convert_workflow(json.loads(workflow_json), domain_id=domain_id, default_email=default_email)
        description, instruction = (gen.get("message") or prompt), prompt
    nodes = workflow["nodes"]
    spec_input = {
        "analysisDomainId": domain_id,
        "agentName": name,
        "analysisDescription": description[:4000],
        "useDeepAnalysis": False,
        "instruction": instruction[:4000],
        "workflow": workflow,
    }
    created = client.create_workflow_agent(spec_input, workspace_id=workspace_id, as_draft=True)
    agent_id = created["id"]
    back = client.get_agent(agent_id, workspace_id=workspace_id) or created
    if back.get("scheduleId") and not back.get("isDraft"):
        client.update_agent_state(agent_id, "INACTIVE", reason="demo creator: created disabled")
        back = client.get_agent(agent_id, workspace_id=workspace_id) or back
    agents = dict(state.wisdom.get("agents") or {})
    agents[key] = {"agent_id": agent_id, "agent_name": name, "is_draft": bool(back.get("isDraft")), "nodes": len(nodes)}
    state.set("wisdom", "agents", agents)
    if first:
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
                    echo: bool = True, entry: dict | None = None) -> LiveAppResult:
    """Mirror the UI: createApp -> conversation with liveAppEditPolicy EDIT ->
    setActiveAppConversation -> one prompt message carrying the app's dashboard
    reference -> wait for the assistant to finish -> read the app back.
    `entry` is one of spec.live_apps (default the first); ids go to state `wisdom.apps[<key>]`,
    the first entry also to the legacy `app_id` / `app_name` / `app_conversation_id`."""
    domain_id = state.wisdom["domain_id"]
    entry = entry or spec.live_app
    key = entry.get("key") or _first_key(spec.live_apps) or "app"
    first = key == (_first_key(spec.live_apps) or key)
    name = entry.get("name") or f"{spec.title} Live App"
    prompt = _prompt_body((spec.dir / entry.get("prompt", "live_app_prompt.md")).read_text())
    apps = dict(state.wisdom.get("apps") or {})
    mine = dict(apps.get(key) or {})
    if first and not mine and state.wisdom.get("app_id"):
        mine = {"app_id": state.wisdom["app_id"], "conversation_id": state.wisdom.get("app_conversation_id")}
    if mine.get("app_id") and not mine.get("conversation_id"):
        app = client.get_app_full(mine["app_id"])  # shell exists from an earlier attempt; build into it
    else:
        app = client.create_app(workspace_id, name, domain_id)
    app_id, dashboard_id = app["id"], app["dashboardId"]

    def _remember(**kw):
        apps[key] = {**(apps.get(key) or {}), "app_id": app_id, "app_name": name, **kw}
        state.set("wisdom", "apps", apps)
        if first:
            state.set("wisdom", "app_id", app_id)
            state.set("wisdom", "app_name", name)
            if "conversation_id" in kw:
                state.set("wisdom", "app_conversation_id", kw["conversation_id"])

    _remember()
    conv_id = client.create_conversation_full(domain_id, hidden=False, workspace_id=workspace_id, live_app_edit_policy="EDIT",
                                              request_channel_type="LIVE_APP", channel_source_id=app_id)
    _remember(conversation_id=conv_id)
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
    # The conversation can finish while the build itself was stopped ("Visualization generation failed",
    # "This response was stopped"): an app with no live spec after the build is a failed build.
    low = (text or "").lower()
    if completed and (back.get("liveSpecVersion") is None or "generation failed" in low or "response was stopped" in low):
        completed = False
    return LiveAppResult(app_id, name, conv_id, dashboard_id, completed, round(time.time() - t0, 1), text,
                         back.get("liveSpecVersion"), back.get("hasUnpublishedChanges"))
