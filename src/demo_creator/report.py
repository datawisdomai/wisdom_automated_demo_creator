"""DEMO_REPORT.md — what exists after a run, with links and ids, plus anything skipped."""
from __future__ import annotations

from datetime import datetime, timezone

from . import config
from .manifest import State
from .spec import DemoSpec

STEP_ORDER = ["generate", "validate", "ddl", "load", "validate_snowflake", "rq_check_snowflake", "metrics_check", "docs",
              "publish.connection", "publish.domain", "publish.database", "publish.federated", "publish.instructions", "publish.knowledge",
              "publish.metrics", "publish.reviewed_queries", "publish.lookup", "publish.documents", "publish.extraction", "publish.skills", "publish.s3_dataset",
              "eval", "health", "app", "chat", "agent"]


def base_url(spec: DemoSpec) -> str:
    dep = config.wisdom_deployment(spec.wisdom.deployment)
    host = dep.host or f"{dep.tenant}.askwisdom.ai"
    return f"https://{host}"


def _slugify(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")


def links(spec: DemoSpec, state: State) -> dict[str, str]:
    """Clickable UI links for everything the build created. URL patterns verified in the
    proddemo UI on 2026-10-13: /apps/<slug>--<app_id>, /agents/<id>/edit, /chat/<conversation>,
    /domains/<id>, /domains/<id>/domain-health, /connections/<id>."""
    w = state.wisdom
    url = base_url(spec)
    out: dict[str, str] = {"Instance": url}
    if w.get("domain_id"):
        out["Domain"] = f"{url}/domains/{w['domain_id']}"
        out["Domain Health"] = f"{url}/domains/{w['domain_id']}/domain-health"
    apps = dict(w.get("apps") or {})
    if w.get("app_id") and not any(a.get("app_id") == w["app_id"] for a in apps.values()):
        apps = {"_legacy": {"app_id": w["app_id"], "app_name": w.get("app_name") or spec.live_app.get("name", "app"), "conversation_id": w.get("app_conversation_id")}, **apps}
    for i, (key, a) in enumerate(apps.items()):
        if not a.get("app_id"):
            continue
        label = "Live App" if i == 0 else f"Live App ({a.get('app_name') or key})"
        out[label] = f"{url}/apps/{_slugify(a.get('app_name') or key)}--{a['app_id']}"
    chats = dict(w.get("chats") or {})
    conv = w.get("followup_conversation_id") or (state.step("chat") or {}).get("conversation_id")
    if conv and not any(c.get("conversation_id") == conv for c in chats.values()):
        chats = {"followup": {"conversation_id": conv}, **chats}
    for i, (key, c) in enumerate(chats.items()):
        if c.get("conversation_id"):
            out["Follow-up chat" if i == 0 else f"Chat ({key})"] = f"{url}/chat/{c['conversation_id']}"
    for i, (key, a) in enumerate(apps.items()):
        if a.get("conversation_id"):
            out["Live App build conversation" if i == 0 else f"Live App build conversation ({a.get('app_name') or key})"] = f"{url}/chat/{a['conversation_id']}"
    agents = dict(w.get("agents") or {})
    if w.get("agent_id") and not any(a.get("agent_id") == w["agent_id"] for a in agents.values()):
        agents = {"_legacy": {"agent_id": w["agent_id"], "agent_name": w.get("agent_name")}, **agents}
    for i, (key, a) in enumerate(agents.items()):
        if a.get("agent_id"):
            out["Agent" if i == 0 else f"Agent ({a.get('agent_name') or key})"] = f"{url}/agents/{a['agent_id']}/edit"
    if w.get("connection_id"):
        out["Connection"] = f"{url}/connections/{w['connection_id']}"
    if w.get("s3_connection_id"):
        out["S3 document archive connection"] = f"{url}/connections/{w['s3_connection_id']}"
    for name, info in (w.get("federated_sources") or {}).items():
        if info.get("connection_id"):
            out[f"Federated connection ({name}, read-only)"] = f"{url}/connections/{info['connection_id']}"
    return out


def _skills_line(w: dict) -> str:
    return ", ".join(f"{n} v{i.get('version')} ({i.get('via')})" for n, i in (w.get("skills") or {}).items())


def render(spec: DemoSpec, state: State) -> str:
    w = state.wisdom
    url = base_url(spec)
    lines = [f"# {spec.title} — demo build report", "",
             f"Built {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · demo as-of {spec.as_of} · seed {spec.seed}", ""]
    lines += ["## Where everything is", "",
              f"| Asset | Value |", "|---|---|",
              f"| Snowflake | `{spec.qualified_schema}` ({len(spec.tables)} tables, {len(spec.snowflake.views)} views) |",
              *[f"| Federated source (read-only) | {f.connection} — `{f.database}` ({len(f.tables)} tables, {f.dialect}) |" for f in spec.wisdom.federated_sources],
              f"| Wisdom deployment / workspace | {spec.wisdom.deployment} / {spec.wisdom.workspace_id} |",
              (f"| Domain | {spec.wisdom.domain_name} — `{w.get('domain_id', '—')}` (EXISTING, shared — this demo added `{spec.qualified_schema}`) |"
               if spec.wisdom.existing_domain else f"| Domain | {spec.wisdom.domain_name} — `{w.get('domain_id', '—')}` |"),
              f"| Live App | {w.get('app_name', spec.live_app.get('name', '—'))} — `{w.get('app_id', 'not created')}` |",
              *[f"| Live App ({a.get('app_name') or k}) | `{a.get('app_id')}` |" for k, a in (w.get("apps") or {}).items() if a.get("app_id") and a.get("app_id") != w.get("app_id")],
              f"| Follow-up chat | `{w.get('followup_conversation_id', 'not asked')}` |",
              *[f"| Chat ({k}) | `{c.get('conversation_id')}` · score {c.get('score')} |" for k, c in (w.get("chats") or {}).items() if c.get("conversation_id") and c.get("conversation_id") != w.get("followup_conversation_id")],
              f"| Agent (disabled) | {w.get('agent_name', spec.agent.get('name', '—'))} — `{w.get('agent_id', 'not created')}` |",
              *[f"| Agent ({a.get('agent_name') or k}) | `{a.get('agent_id')}` |" for k, a in (w.get("agents") or {}).items() if a.get("agent_id") and a.get("agent_id") != w.get("agent_id")],
              *([f"| Skills | {_skills_line(w)} |"] if w.get("skills") else []),
              f"| Eval | set `{w.get('eval_set_id', '—')}` · last score {w.get('last_score', '—')} |",
              f"| Domain Health run | job `{w.get('health_job_run_id', 'not triggered')}` (review in the Domain Health tab) |",
              f"| Documents | {len(w.get('uploaded_documents') or [])} uploaded"
              + (f"; S3 dataset `{w['s3_dataset_id']}` on connection `{w.get('s3_connection_id')}`" if w.get('s3_dataset_id') else "") + " |",
              f"| Instance | {url} |", ""]
    lines += ["## Links", ""]
    for label, href in links(spec, state).items():
        lines.append(f"- **{label}**: {href}")
    lines.append("")
    lines += ["## Steps", "", "| Step | Status | When | Notes |", "|---|---|---|---|"]
    for step in STEP_ORDER + [s for s in state.data["steps"] if s not in STEP_ORDER]:
        info = state.data["steps"].get(step)
        if not info:
            continue
        notes = {k: v for k, v in info.items() if k not in ("status", "at")}
        note = ", ".join(f"{k}={str(v)[:60]}" for k, v in list(notes.items())[:4])
        lines.append(f"| {step} | {info.get('status')} | {str(info.get('at', ''))[:16]} | {note} |")
    lines.append("")
    skipped = [s for s in ("app", "chat", "agent", "eval") if not state.data["steps"].get(s)]
    manual = list(spec.manual_steps)
    if skipped or manual:
        lines += ["## Still to do by hand", ""]
        for s in skipped:
            lines.append(f"- `{s}` step has not run (`demo {s} {spec.name} --apply`)")
        for m in manual:
            if isinstance(m, dict):
                lines.append(f"- {m.get('kind', 'step')}: {', '.join(f'{k}={v}' for k, v in m.items() if k != 'kind')}")
            else:  # a plain sentence in demo.yaml is fine too
                lines.append(f"- {m}")
        lines.append("")
    lines += ["## Control points in the data", ""]
    for cp in spec.control_points:
        lines.append(f"- **{cp.id}** {cp.name}" + (f" (hero: {cp.hero})" if cp.hero else ""))
    lines.append("")
    qs = [c.get("followup_question") for c in spec.chats if c.get("followup_question")]
    if qs:
        lines += ["## Follow-up question" + ("s" if len(qs) > 1 else ""), ""] + [f"> {q}" + "\n" for q in qs]
    return "\n".join(lines)
